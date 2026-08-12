from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _optional_int(name: str) -> int | None:
    value = os.getenv(name, "").strip()
    return int(value) if value else None


@dataclass(frozen=True, slots=True)
class Settings:
    discord_token: str
    dev_guild_id: int | None
    tts_voice: str
    tts_language: str
    tts_speed: float
    tts_steps: int
    tts_max_chars: int
    voice_settings_path: str
    emoji_webhook_name: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token:
            raise RuntimeError("DISCORD_TOKEN이 설정되지 않았습니다.")

        voice = os.getenv("TTS_VOICE", "F1").strip().upper()
        if voice not in {f"{gender}{number}" for gender in "MF" for number in range(1, 6)}:
            raise RuntimeError("TTS_VOICE는 M1-M5 또는 F1-F5 중 하나여야 합니다.")

        speed = float(os.getenv("TTS_SPEED", "1.05"))
        steps = int(os.getenv("TTS_STEPS", "8"))
        if not 0.7 <= speed <= 2.0:
            raise RuntimeError("TTS_SPEED는 0.7 이상 2.0 이하여야 합니다.")
        if not 5 <= steps <= 12:
            raise RuntimeError("TTS_STEPS는 5 이상 12 이하여야 합니다.")

        max_chars = int(os.getenv("TTS_MAX_CHARS", "500"))
        if max_chars < 1:
            raise RuntimeError("TTS_MAX_CHARS는 1 이상이어야 합니다.")
        voice_settings_path = os.getenv(
            "VOICE_SETTINGS_PATH", "data/voice_preferences.json"
        ).strip()
        if not voice_settings_path:
            raise RuntimeError("VOICE_SETTINGS_PATH는 비워 둘 수 없습니다.")

        return cls(
            discord_token=token,
            dev_guild_id=_optional_int("DEV_GUILD_ID"),
            tts_voice=voice,
            tts_language=os.getenv("TTS_LANGUAGE", "ko").strip() or "ko",
            tts_speed=speed,
            tts_steps=steps,
            tts_max_chars=max_chars,
            voice_settings_path=voice_settings_path,
            emoji_webhook_name=os.getenv("EMOJI_WEBHOOK_NAME", "DotoriBot Emoji").strip(),
        )
