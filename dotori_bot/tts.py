from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import discord
import numpy as np


DISCORD_SAMPLE_RATE = 48_000
DISCORD_FRAME_BYTES = 3_840  # 20 ms, 48 kHz, signed 16-bit, stereo
LOGGER = logging.getLogger("dotoribot.voice")


def float_audio_to_discord_pcm(wav: np.ndarray, source_rate: int) -> bytes:
    """Convert mono/stereo floating-point audio to Discord's PCM format."""
    samples = np.asarray(wav, dtype=np.float32).squeeze()
    if samples.ndim != 1:
        raise ValueError("TTS 출력은 단일 오디오 스트림이어야 합니다.")
    if samples.size == 0:
        raise ValueError("TTS가 빈 오디오를 생성했습니다.")

    if source_rate != DISCORD_SAMPLE_RATE:
        output_size = max(1, round(samples.size * DISCORD_SAMPLE_RATE / source_rate))
        source_positions = np.arange(samples.size, dtype=np.float64)
        target_positions = np.linspace(0, samples.size - 1, output_size)
        samples = np.interp(target_positions, source_positions, samples).astype(np.float32)

    mono = (np.clip(samples, -1.0, 1.0) * 32767.0).astype("<i2")
    stereo = np.column_stack((mono, mono)).reshape(-1)
    return stereo.tobytes()


class PCMBytesAudioSource(discord.AudioSource):
    def __init__(self, pcm: bytes) -> None:
        self._pcm = memoryview(pcm)
        self._offset = 0

    def read(self) -> bytes:
        if self._offset >= len(self._pcm):
            return b""
        end = min(self._offset + DISCORD_FRAME_BYTES, len(self._pcm))
        frame = self._pcm[self._offset:end].tobytes()
        self._offset = end
        if len(frame) < DISCORD_FRAME_BYTES:
            frame += b"\0" * (DISCORD_FRAME_BYTES - len(frame))
        return frame

    def is_opus(self) -> bool:
        return False


class SupertonicService:
    def __init__(self, *, voice: str, language: str, speed: float, steps: int) -> None:
        self.voice = voice
        self.language = language
        self.speed = speed
        self.steps = steps
        self._tts: Any = None
        self._style: Any = None
        self._lock = asyncio.Lock()

    def _synthesize_sync(self, text: str) -> bytes:
        if self._tts is None:
            from supertonic import TTS

            self._tts = TTS(auto_download=True)
            self._style = self._tts.get_voice_style(voice_name=self.voice)

        wav, _duration = self._tts.synthesize(
            text=text,
            voice_style=self._style,
            lang=self.language,
            total_steps=self.steps,
            speed=self.speed,
        )
        return float_audio_to_discord_pcm(wav, int(self._tts.sample_rate))

    async def synthesize(self, text: str) -> bytes:
        # ONNX 세션과 음성 스타일은 공유하되 동시 접근은 직렬화한다.
        async with self._lock:
            return await asyncio.to_thread(self._synthesize_sync, text)


@dataclass(slots=True)
class AudioJob:
    pcm: bytes


class VoiceQueueManager:
    def __init__(self, idle_seconds: int) -> None:
        self.idle_seconds = idle_seconds
        self._queues: dict[int, asyncio.Queue[AudioJob]] = {}
        self._workers: dict[int, asyncio.Task[None]] = {}

    def enqueue(self, voice_client: discord.VoiceClient, job: AudioJob) -> int:
        guild_id = voice_client.guild.id
        queue = self._queues.setdefault(guild_id, asyncio.Queue())
        ahead = queue.qsize() + int(voice_client.is_playing())
        queue.put_nowait(job)
        worker = self._workers.get(guild_id)
        if worker is None or worker.done():
            self._workers[guild_id] = asyncio.create_task(
                self._run(guild_id, voice_client), name=f"voice-queue-{guild_id}"
            )
        return ahead

    async def stop(self, guild_id: int, voice_client: discord.VoiceClient) -> None:
        """Stop current playback, discard queued audio, and disconnect."""
        worker = self._workers.pop(guild_id, None)
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        if worker is not None and worker is not asyncio.current_task():
            worker.cancel()
            await asyncio.gather(worker, return_exceptions=True)

        self._queues.pop(guild_id, None)
        if voice_client.is_connected():
            await voice_client.disconnect(force=True)

    async def _run(self, guild_id: int, voice_client: discord.VoiceClient) -> None:
        queue = self._queues[guild_id]
        try:
            while True:
                try:
                    job = await asyncio.wait_for(queue.get(), timeout=self.idle_seconds)
                except asyncio.TimeoutError:
                    if voice_client.is_connected():
                        await voice_client.disconnect()
                    return

                try:
                    if not voice_client.is_connected():
                        continue
                    finished = asyncio.get_running_loop().create_future()

                    def after(error: Exception | None) -> None:
                        loop = finished.get_loop()

                        def complete() -> None:
                            if finished.done():
                                return
                            if error:
                                finished.set_exception(error)
                            else:
                                finished.set_result(None)

                        loop.call_soon_threadsafe(complete)

                    voice_client.play(PCMBytesAudioSource(job.pcm), after=after)
                    await finished
                except Exception:
                    LOGGER.exception("서버 %s에서 음성 재생에 실패했습니다.", guild_id)
                finally:
                    queue.task_done()
        finally:
            self._queues.pop(guild_id, None)
            self._workers.pop(guild_id, None)
