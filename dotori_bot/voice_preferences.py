from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path


LOGGER = logging.getLogger("dotoribot.voice_preferences")
VOICE_NAMES = tuple(f"{gender}{number}" for gender in "MF" for number in range(1, 6))


class VoicePreferenceStore:
    def __init__(self, path: str | Path, default_voice: str) -> None:
        self.path = Path(path)
        self.default_voice = default_voice
        self._preferences: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            users = data.get("users", {})
            if isinstance(users, dict):
                self._preferences = {
                    str(user_id): voice
                    for user_id, voice in users.items()
                    if voice in VOICE_NAMES
                }
        except (OSError, json.JSONDecodeError):
            LOGGER.exception("목소리 설정 파일 %s을 읽지 못했습니다.", self.path)

    def get(self, user_id: int) -> str:
        return self._preferences.get(str(user_id), self.default_voice)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = {"version": 1, "users": self._preferences}
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(self.path)

    async def set(self, user_id: int, voice: str) -> None:
        if voice not in VOICE_NAMES:
            raise ValueError(f"지원하지 않는 목소리입니다: {voice}")
        async with self._lock:
            self._preferences[str(user_id)] = voice
            await asyncio.to_thread(self._save)
