from typing import Callable, Optional

import pyaudio
import riva.client

from robot_sync_app.ports.speech_port import SpeechPort


class RivaSpeechAdapter(SpeechPort):
    def __init__(
        self,
        server: str,
        voice_name: str,
        sample_rate_hz: int,
        output_device_index: Optional[int],
        output_device_name_hint: str = "KT USB Audio",
    ) -> None:
        self._server = server
        self._voice = voice_name
        self._rate = sample_rate_hz
        self._output_device_index = output_device_index
        self._output_device_name_hint = output_device_name_hint

    def _resolve_output_device(self, p: pyaudio.PyAudio) -> Optional[int]:
        """Resolve output device using explicit index or name hint"""
        # Try explicit device index first (highest priority)
        if self._output_device_index is not None:
            print(f"✓ Using explicitly configured output device index: {self._output_device_index}")
            return self._output_device_index

        # Try to find by name hint (e.g., KT USB Audio)
        hint = self._output_device_name_hint.lower()
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info.get("maxOutputChannels", 0) > 0 and hint in info.get("name", "").lower():
                print(f"✓ Found output device '{info['name']}' on index {i}")
                return i

        # Fallback to system default output device
        print(f"⚠️ Output device hint '{self._output_device_name_hint}' not found, using system default")
        default_device = p.get_default_output_device_info()
        print(f"✓ Using default output device: {default_device['name']} (index {default_device['index']})")
        return default_device['index']

    def speak(self, text: str, on_start: Callable[[], None], on_end: Callable[[], None]) -> None:
        auth = riva.client.Auth(uri=self._server)
        tts = riva.client.SpeechSynthesisService(auth)

        on_start()
        try:
            resp = tts.synthesize(
                text=text,
                language_code="en-US",
                encoding=riva.client.AudioEncoding.LINEAR_PCM,
                sample_rate_hz=self._rate,
                voice_name=self._voice,
            )
            p = pyaudio.PyAudio()
            device_index = self._resolve_output_device(p)

            # Build stream parameters, only include device index if not None
            stream_params = {
                "format": pyaudio.paInt16,
                "channels": 1,
                "rate": self._rate,
                "output": True,
            }
            if device_index is not None:
                stream_params["output_device_index"] = device_index

            stream = p.open(**stream_params)
            stream.write(resp.audio)
            stream.stop_stream()
            stream.close()
            p.terminate()
        finally:
            on_end()
