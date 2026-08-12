from dotori_bot.bot import (
    channel_has_humans,
    leave_command,
    leave_korean_command,
    speak_korean_command,
    tts_command,
    voice_command,
    voice_korean_command,
)


class FakeMember:
    def __init__(self, *, bot: bool) -> None:
        self.bot = bot


class FakeChannel:
    def __init__(self, members: list[FakeMember]) -> None:
        self.members = members


def test_slash_command_names_and_parameters() -> None:
    assert tts_command.name == "tts"
    assert [parameter.name for parameter in tts_command.parameters] == ["text"]
    assert speak_korean_command.name == "말"
    assert [parameter.name for parameter in speak_korean_command.parameters] == ["내용"]
    assert leave_command.name == "leave"
    assert leave_korean_command.name == "퇴장"
    assert voice_command.name == "voice"
    assert [parameter.name for parameter in voice_command.parameters] == ["voice"]
    assert voice_korean_command.name == "목소리"
    assert [parameter.name for parameter in voice_korean_command.parameters] == ["목소리"]


def test_channel_human_detection() -> None:
    assert channel_has_humans(FakeChannel([FakeMember(bot=False)]))
    assert not channel_has_humans(FakeChannel([]))
    assert not channel_has_humans(FakeChannel([FakeMember(bot=True)]))
