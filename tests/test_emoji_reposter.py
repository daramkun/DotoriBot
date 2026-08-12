from dotori_bot.emoji_reposter import single_emoji_asset


def test_static_custom_emoji() -> None:
    asset = single_emoji_asset("<:acorn:123456789012345678>")
    assert asset is not None
    assert asset.filename == "emoji.png"
    assert "/123456789012345678.png" in asset.url


def test_animated_custom_emoji() -> None:
    asset = single_emoji_asset("  <a:dance:123456789012345678>\n")
    assert asset is not None
    assert asset.filename == "emoji.gif"


def test_rejects_unicode_text_or_multiple_emoji() -> None:
    assert single_emoji_asset("😀") is None
    assert single_emoji_asset("👨‍👩‍👧‍👦") is None
    assert single_emoji_asset("안녕 👋") is None
    assert single_emoji_asset("😀😀") is None
    assert single_emoji_asset(
        "<:one:123456789012345678><:two:223456789012345678>"
    ) is None
    assert single_emoji_asset("hello") is None
