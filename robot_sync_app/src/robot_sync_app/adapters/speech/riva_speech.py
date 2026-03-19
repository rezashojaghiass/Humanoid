import logging
from typing import Callable, Optional

import pyaudio
import riva.client

from robot_sync_app.ports.speech_port import SpeechPort

logger = logging.getLogger(__name__)


def find_output_device_by_name(target_name: str = "KT USB Audio") -> Optional[int]:
    """Find output device by name (case-insensitive)"""
    logger.info(f"Searching for device: {target_name}")
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    
    for i in range(device_count):
        try:
            info = p.get_device_info_by_index(i)
            max_output_channels = info.get('maxOutputChannels', 0)
            
            if max_output_channels > 0:  # This is an output device
                device_name = info.get('name', '')
                if target_name.lower() in device_name.lower():
                    logger.info(f"Found {target_name} at device {i}")
                    p.terminate()
                    return i
        except Exception as e:
            logger.debug(f"Error checking device {i}: {e}")
            continue
    
    logger.warning(f"Device {target_name} not found")
    p.terminate()
    return None


class RivaSpeechAdapter(SpeechPort):
    def __init__(self, server: str, voice_name: str, sample_rate_hz: int, output_device_index: Optional[int] = None, output_device_name_hint: str = "KT USB Audio") -> None:
        logger.info(f"Initializing RivaSpeechAdapter: server={server}, voice={voice_name}, rate={sample_rate_hz}, device={output_device_index}, hint={output_device_name_hint}")
        self._server = server
        self._voice = voice_name
        self._rate = sample_rate_hz
        self._output_device_index = output_device_index
        self._output_device_name_hint = output_device_name_hint
        
        # Auto-detect output device if index is None
        if output_device_index is None:
            logger.info(f"Device index is None, auto-detecting using hint: {output_device_name_hint}")
            detected = find_output_device_by_name(output_device_name_hint)
            if detected is not None:
                self._out = detected
                logger.info(f"Auto-detected KT USB Audio speaker at device {detected}")
            else:
                logger.warning("KT USB Audio speaker not found, using default device")
                self._out = None
        else:
            self._out = output_device_index
            logger.info(f"Using specified device: {self._out}")

    def speak(self, text: str, on_start: Callable[[], None], on_end: Callable[[], None]) -> None:
        logger.info(f"speak() called with text: {text[:50]}...")
        print(f"🔊 TTS: Speaking... ({text[:40]}...)", flush=True)
        auth = riva.client.Auth(uri=self._server)
        tts = riva.client.SpeechSynthesisService(auth)

        on_start()
        p = None
        stream = None
        try:
            logger.info(f"Synthesizing with device={self._out}, rate={self._rate}")
            resp = tts.synthesize(
                text=text,
                language_code="en-US",
                encoding=riva.client.AudioEncoding.LINEAR_PCM,
                sample_rate_hz=self._rate,
                voice_name=self._voice,
            )
            audio_bytes = resp.audio
            logger.info(f"Synthesis complete, got {len(audio_bytes)} bytes")
            print(f"✓ TTS synthesis complete: {len(audio_bytes)} bytes", flush=True)
            
            # Calculate audio duration in seconds
            # PCM audio: 2 bytes per sample (16-bit), 1 channel (mono)
            bytes_per_sample = 2
            num_samples = len(audio_bytes) // bytes_per_sample
            audio_duration_sec = num_samples / self._rate
            logger.info(f"Audio duration: {audio_duration_sec:.2f}s ({num_samples} samples at {self._rate}Hz)")
            print(f"⏱️  Audio duration: {audio_duration_sec:.2f}s", flush=True)
            
            p = pyaudio.PyAudio()
            logger.info(f"PyAudio initialized")
            
            # Riva synthesizes MONO audio (1 channel), so always use mono for playback
            logger.info(f"Opening stream with 1 channel (mono) on device {self._out}")
            
            # Build stream parameters
            stream_params = {
                "format": pyaudio.paInt16,
                "channels": 1,  # Riva outputs mono, not stereo
                "rate": self._rate,
                "output": True,
            }
            # Only specify device if explicitly set
            if self._out is not None:
                stream_params["output_device_index"] = self._out
            
            stream = p.open(**stream_params)
            logger.info(f"Stream opened successfully")
            
            logger.info(f"Writing {len(audio_bytes)} bytes to stream")
            print(f"▶️  Playing audio ({len(audio_bytes)} bytes)...", flush=True)
            
            # Write audio to stream - stream.write() is blocking
            # The caller should be animating the face during this time
            # Pass the duration so animation can loop appropriately
            # Store it on the adapter so the face can access it
            self._last_audio_duration = audio_duration_sec
            
            stream.write(audio_bytes)
            stream.stop_stream()
            stream.close()
            logger.info(f"Audio playback complete")
            print(f"✓ Audio playback complete", flush=True)
        except Exception as e:
            logger.error(f"Error in speak(): {e}", exc_info=True)
            raise
        finally:
            if p:
                p.terminate()
            on_end()
