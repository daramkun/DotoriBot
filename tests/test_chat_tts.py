from dotori_bot.chat_tts import ChatTTSSessions, split_tts_text


def test_chat_tts_session_is_scoped_to_user_guild_and_channel() -> None:
    sessions = ChatTTSSessions()
    sessions.start(1, 2, 3)

    assert sessions.matches(1, 2, 3)
    assert not sessions.matches(1, 2, 4)
    assert not sessions.matches(1, 5, 3)
    assert sessions.stop(1, 2)
    assert not sessions.stop(1, 2)


def test_clear_guild_only_removes_that_guild() -> None:
    sessions = ChatTTSSessions()
    sessions.start(1, 2, 3)
    sessions.start(2, 2, 3)

    sessions.clear_guild(1)

    assert not sessions.matches(1, 2, 3)
    assert sessions.matches(2, 2, 3)


def test_split_tts_text_preserves_long_message() -> None:
    text = "가나다라 마바사아 자차카타"
    chunks = split_tts_text(text, 6)

    assert chunks == ["가나다라", "마바사아", "자차카타"]
    assert " ".join(chunks) == text
