from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO

import aiohttp
import discord


CUSTOM_EMOJI_RE = re.compile(r"^<(a?):([A-Za-z0-9_]{2,32}):(\d{15,22})>$")


@dataclass(frozen=True, slots=True)
class EmojiAsset:
    url: str
    filename: str


def single_emoji_asset(content: str) -> EmojiAsset | None:
    candidate = content.strip()
    custom = CUSTOM_EMOJI_RE.fullmatch(candidate)
    if custom is None:
        return None
    animated, _name, emoji_id = custom.groups()
    extension = "gif" if animated else "png"
    return EmojiAsset(
        url=f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}?size=256&quality=lossless",
        filename=f"emoji.{extension}",
    )


class EmojiReposter:
    def __init__(self, bot: discord.Client, webhook_name: str) -> None:
        self.bot = bot
        self.webhook_name = webhook_name
        self._webhooks: dict[int, discord.Webhook] = {}

    async def _webhook_for(self, channel: discord.abc.GuildChannel) -> discord.Webhook:
        cached = self._webhooks.get(channel.id)
        if cached is not None:
            return cached

        webhooks = await channel.webhooks()
        webhook = next((item for item in webhooks if item.name == self.webhook_name), None)
        if webhook is None:
            webhook = await channel.create_webhook(
                name=self.webhook_name,
                reason="이모지 이미지를 원 작성자의 이름으로 다시 게시",
            )
        self._webhooks[channel.id] = webhook
        return webhook

    async def handle(self, message: discord.Message) -> None:
        if message.guild is None or message.author.bot or message.webhook_id is not None:
            return
        if message.attachments or message.stickers:
            return
        asset = single_emoji_asset(message.content)
        if asset is None:
            return

        thread: discord.Thread | None = None
        if isinstance(message.channel, discord.Thread):
            thread = message.channel
            webhook_channel = message.channel.parent
        else:
            webhook_channel = message.channel
        if webhook_channel is None or not hasattr(webhook_channel, "webhooks"):
            return

        webhook = await self._webhook_for(webhook_channel)
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(asset.url) as response:
                response.raise_for_status()
                image = await response.read()

        send_options = {
            "username": message.author.display_name[:80],
            "avatar_url": message.author.display_avatar.url,
            "file": discord.File(fp=BytesIO(image), filename=asset.filename),
            "allowed_mentions": discord.AllowedMentions.none(),
            "wait": True,
        }
        if thread is not None:
            send_options["thread"] = thread

        # 먼저 재게시해 두면 네트워크 오류 때문에 원본만 사라지는 일을 피할 수 있다.
        reposted = await webhook.send(**send_options)
        try:
            await message.delete()
        except discord.HTTPException:
            if isinstance(reposted, discord.WebhookMessage):
                await reposted.delete()
            raise
