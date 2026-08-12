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


def test_unicode_emoji() -> None:
    asset = single_emoji_asset("👨‍👩‍👧‍👦")
    assert asset is not None
    assert "1f468-200d-1f469-200d-1f467-200d-1f466" in asset.url


def test_rejects_text_or_multiple_emoji() -> None:
    assert single_emoji_asset("안녕 👋") is None
    assert single_emoji_asset("😀😀") is None
    assert single_emoji_asset("hello") is None
