from dotori_bot.bot import leave_command, leave_korean_command, speak_korean_command, tts_command


def test_slash_command_names_and_parameters() -> None:
    assert tts_command.name == "tts"
    assert [parameter.name for parameter in tts_command.parameters] == ["text"]
    assert speak_korean_command.name == "말"
    assert [parameter.name for parameter in speak_korean_command.parameters] == ["내용"]
    assert leave_command.name == "leave"
    assert leave_korean_command.name == "퇴장"
