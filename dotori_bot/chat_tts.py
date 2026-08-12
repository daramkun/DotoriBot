from __future__ import annotations


class ChatTTSSessions:
    """Track which text channel each user has enabled for automatic TTS."""

    def __init__(self) -> None:
        self._channels: dict[tuple[int, int], int] = {}

    def start(self, guild_id: int, user_id: int, channel_id: int) -> None:
        self._channels[(guild_id, user_id)] = channel_id

    def stop(self, guild_id: int, user_id: int) -> bool:
        return self._channels.pop((guild_id, user_id), None) is not None

    def matches(self, guild_id: int, user_id: int, channel_id: int) -> bool:
        return self._channels.get((guild_id, user_id)) == channel_id

    def clear_guild(self, guild_id: int) -> None:
        keys = [key for key in self._channels if key[0] == guild_id]
        for key in keys:
            del self._channels[key]


def split_tts_text(text: str, max_chars: int) -> list[str]:
    """Split a Discord message without dropping any non-whitespace text."""
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    while len(text) > max_chars:
        boundary = max(
            text.rfind("\n", 0, max_chars + 1),
            text.rfind(" ", 0, max_chars + 1),
        )
        if boundary <= 0:
            boundary = max_chars
        chunks.append(text[:boundary].strip())
        text = text[boundary:].strip()
    if text:
        chunks.append(text)
    return chunks
