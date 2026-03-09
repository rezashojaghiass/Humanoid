import audioop
import math
import struct
from typing import List, Optional

import pyaudio
import riva.client

from robot_sync_app.ports.asr_port import ASRPort


class RivaMicASRAdapter(ASRPort):
    def __init__(
        self,
        server: str,
        input_device_index: Optional[int],
        input_device_name_hint: str,
        max_duration_sec: int,
        silence_threshold: int,
        silence_duration_sec: float,
        sample_rate_hz: int = 16000,
    ) -> None:
        self._server = server
        self._input_device_index = input_device_index
        self._input_device_name_hint = input_device_name_hint
        self._max_duration = max_duration_sec
        self._silence_threshold = silence_threshold
        self._silence_duration = silence_duration_sec
        self._target_rate = sample_rate_hz

    def _resolve_input_device(self, p: pyaudio.PyAudio) -> Optional[int]:
        if self._input_device_index is not None:
            return self._input_device_index

        hint = self._input_device_name_hint.lower()
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0 and hint in info.get("name", "").lower():
                print(f"✓ Found input device '{info['name']}' on index {i}")
                return i
        return None

    def _record_with_vad(self) -> bytes:
        p = pyaudio.PyAudio()
        device_index = self._resolve_input_device(p)

        hw_rate = 48000
        chunk = 1024
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=hw_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=chunk,
        )

        print(f"🎤 Listening (max {self._max_duration}s, auto-stop on silence)...")
        frames: List[bytes] = []
        silence_frames = 0
        silence_threshold_frames = int(self._silence_duration * hw_rate / chunk)
        has_speech = False

        for _ in range(int(hw_rate / chunk * self._max_duration)):
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)

            count = len(data) // 2
            samples = struct.unpack(f"{count}h", data)
            rms = math.sqrt(sum(s * s for s in samples) / max(1, count))

            if rms > self._silence_threshold:
                has_speech = True
                silence_frames = 0
            elif has_speech:
                silence_frames += 1

            if has_speech and silence_frames > silence_threshold_frames:
                print("✓ Silence detected, stopping capture")
                break

        stream.stop_stream()
        stream.close()
        p.terminate()

        audio_48k = b"".join(frames)
        audio_16k, _ = audioop.ratecv(audio_48k, 2, 1, hw_rate, self._target_rate, None)
        return audio_16k

    def _transcribe(self, audio_data: bytes) -> str:
        auth = riva.client.Auth(uri=self._server)
        asr = riva.client.ASRService(auth)

        config = riva.client.StreamingRecognitionConfig(
            config=riva.client.RecognitionConfig(
                encoding=riva.client.AudioEncoding.LINEAR_PCM,
                sample_rate_hertz=self._target_rate,
                language_code="en-US",
                max_alternatives=1,
                enable_automatic_punctuation=True,
            ),
            interim_results=False,
        )

        def chunks() -> bytes:
            chunk_size = 1600
            for i in range(0, len(audio_data), chunk_size):
                yield audio_data[i : i + chunk_size]

        final_text = ""
        responses = asr.streaming_response_generator(chunks(), config)
        for response in responses:
            for result in response.results:
                if result.is_final:
                    final_text = result.alternatives[0].transcript.strip()

        return final_text

    def listen_and_transcribe(self) -> str:
        audio = self._record_with_vad()
        text = self._transcribe(audio)
        if text:
            print(f"📝 User said: {text}")
        return text
