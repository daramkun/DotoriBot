import numpy as np

from dotori_bot.tts import DISCORD_FRAME_BYTES, PCMBytesAudioSource, float_audio_to_discord_pcm


def test_audio_is_resampled_to_48khz_stereo_s16() -> None:
    one_second = np.zeros((1, 44_100), dtype=np.float32)
    pcm = float_audio_to_discord_pcm(one_second, 44_100)
    assert len(pcm) == 48_000 * 2 * 2


def test_audio_source_returns_full_discord_frames() -> None:
    source = PCMBytesAudioSource(b"\x01" * (DISCORD_FRAME_BYTES + 10))
    assert len(source.read()) == DISCORD_FRAME_BYTES
    assert len(source.read()) == DISCORD_FRAME_BYTES
    assert source.read() == b""
