import json

import pytest

from dotori_bot.voice_preferences import VoicePreferenceStore


@pytest.mark.asyncio
async def test_voice_preference_persists(tmp_path) -> None:
    path = tmp_path / "voices.json"
    store = VoicePreferenceStore(path, "F1")

    assert store.get(123) == "F1"
    await store.set(123, "M3")

    restored = VoicePreferenceStore(path, "F1")
    assert restored.get(123) == "M3"
    assert json.loads(path.read_text(encoding="utf-8"))["users"] == {"123": "M3"}


@pytest.mark.asyncio
async def test_voice_preference_rejects_unknown_voice(tmp_path) -> None:
    store = VoicePreferenceStore(tmp_path / "voices.json", "F1")
    with pytest.raises(ValueError):
        await store.set(123, "X1")
