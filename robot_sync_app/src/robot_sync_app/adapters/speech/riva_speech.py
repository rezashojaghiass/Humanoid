from typing import Callable

import pyaudio
import riva.client

from robot_sync_app.ports.speech_port import SpeechPort


class RivaSpeechAdapter(SpeechPort):
    def __init__(self, server: str, voice_name: str, sample_rate_hz: int, output_device_index: int) -> None:
        self._server = server
        self._voice = voice_name
        self._rate = sample_rate_hz
        self._out = output_device_index

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
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self._rate,
                output=True,
                output_device_index=self._out,
            )
            stream.write(resp.audio)
            stream.stop_stream()
            stream.close()
            p.terminate()
        finally:
            on_end()
