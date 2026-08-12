from __future__ import annotations

import logging

import discord
from discord import app_commands

from .config import Settings
from .emoji_reposter import EmojiReposter
from .tts import AudioJob, SupertonicService, VoiceQueueManager
from .voice_preferences import VoicePreferenceStore


LOGGER = logging.getLogger("dotoribot")


def channel_has_humans(channel: discord.abc.Connectable) -> bool:
    members = getattr(channel, "members", ())
    return any(not member.bot for member in members)


class DotoriBot(discord.Client):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.settings = settings
        self.tree = app_commands.CommandTree(self)
        self.tts = SupertonicService(
            voice=settings.tts_voice,
            language=settings.tts_language,
            speed=settings.tts_speed,
            steps=settings.tts_steps,
        )
        self.voice_queues = VoiceQueueManager()
        self.voice_preferences = VoicePreferenceStore(
            settings.voice_settings_path, settings.tts_voice
        )
        self.emoji_reposter = EmojiReposter(self, settings.emoji_webhook_name)

    async def setup_hook(self) -> None:
        self.tree.add_command(tts_command)
        self.tree.add_command(speak_korean_command)
        self.tree.add_command(leave_command)
        self.tree.add_command(leave_korean_command)
        self.tree.add_command(voice_command)
        self.tree.add_command(voice_korean_command)
        if self.settings.dev_guild_id:
            guild = discord.Object(id=self.settings.dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            LOGGER.info("개발 서버 %s에 명령을 동기화했습니다.", guild.id)
        else:
            await self.tree.sync()
            LOGGER.info("전역 명령을 동기화했습니다.")

    async def on_ready(self) -> None:
        LOGGER.info("%s로 로그인했습니다.", self.user)

    async def on_message(self, message: discord.Message) -> None:
        try:
            await self.emoji_reposter.handle(message)
        except discord.Forbidden:
            LOGGER.warning("메시지 %s 처리 권한이 없습니다.", message.id)
        except discord.HTTPException:
            LOGGER.exception("메시지 %s의 이모지 재게시 중 오류가 발생했습니다.", message.id)

    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        voice_client = member.guild.voice_client
        if voice_client is None or not voice_client.is_connected():
            return
        channel = voice_client.channel
        if channel is None or channel_has_humans(channel):
            return

        LOGGER.info("서버 %s의 음성 채널에 사람이 없어 자동 퇴장합니다.", member.guild.id)
        try:
            await self.voice_queues.stop(member.guild.id, voice_client)
        except Exception:
            LOGGER.exception("빈 음성 채널에서 자동 퇴장하지 못했습니다.")


async def _handle_tts(interaction: discord.Interaction, text: str) -> None:
    bot = interaction.client
    if not isinstance(bot, DotoriBot):
        return
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("서버 안에서만 사용할 수 있어요.", ephemeral=True)
        return
    if not text.strip():
        await interaction.response.send_message("읽을 내용을 입력해 주세요.", ephemeral=True)
        return
    if len(text) > bot.settings.tts_max_chars:
        await interaction.response.send_message(
            f"한 번에 {bot.settings.tts_max_chars}자까지만 읽을 수 있어요.", ephemeral=True
        )
        return
    if interaction.user.voice is None or interaction.user.voice.channel is None:
        await interaction.response.send_message("먼저 음성 채널에 들어가 주세요.", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    await interaction.response.defer(ephemeral=True, thinking=True)
    voice_client = interaction.guild.voice_client
    try:
        if voice_client is None:
            voice_client = await channel.connect()
        elif voice_client.channel != channel:
            if voice_client.is_playing():
                await interaction.edit_original_response(
                    content=f"지금 {voice_client.channel.mention}에서 재생 중이에요."
                )
                return
            await voice_client.move_to(channel)

        voice = bot.voice_preferences.get(interaction.user.id)
        pcm = await bot.tts.synthesize(text.strip(), voice=voice)
        if not voice_client.is_connected() or not channel_has_humans(channel):
            await interaction.edit_original_response(
                content="음성을 만드는 동안 채널에 사람이 없어 자동으로 나왔어요."
            )
            return
        ahead = bot.voice_queues.enqueue(voice_client, AudioJob(pcm=pcm))
        status = (
            f"{voice} 목소리로 바로 읽을게요."
            if ahead == 0
            else f"{voice} 목소리로 대기열에 추가했어요. 앞에 {ahead}개가 있어요."
        )
        await interaction.edit_original_response(content=status)
    except discord.Forbidden:
        await interaction.edit_original_response(content="음성 채널에 연결하거나 말할 권한이 없어요.")
    except Exception:
        LOGGER.exception("TTS 명령 처리 중 오류가 발생했습니다.")
        await interaction.edit_original_response(
            content="음성을 만드는 중 오류가 발생했어요. 서버 로그를 확인해 주세요."
        )


async def _handle_leave(interaction: discord.Interaction) -> None:
    bot = interaction.client
    if not isinstance(bot, DotoriBot):
        return
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("서버 안에서만 사용할 수 있어요.", ephemeral=True)
        return

    voice_client = interaction.guild.voice_client
    if voice_client is None or not voice_client.is_connected():
        await interaction.response.send_message("현재 들어가 있는 음성 채널이 없어요.", ephemeral=True)
        return

    user_channel = interaction.user.voice.channel if interaction.user.voice else None
    if user_channel != voice_client.channel and not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "봇과 같은 음성 채널에 들어가 있어야 퇴장시킬 수 있어요.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True, thinking=True)
    try:
        await bot.voice_queues.stop(interaction.guild.id, voice_client)
        await interaction.edit_original_response(content="재생 대기열을 비우고 음성 채널에서 나왔어요.")
    except Exception:
        LOGGER.exception("음성 채널 퇴장 중 오류가 발생했습니다.")
        await interaction.edit_original_response(content="음성 채널에서 나오는 중 오류가 발생했어요.")


async def _handle_voice(interaction: discord.Interaction, voice: str) -> None:
    bot = interaction.client
    if not isinstance(bot, DotoriBot):
        return
    try:
        await bot.voice_preferences.set(interaction.user.id, voice)
        await interaction.response.send_message(
            f"앞으로 TTS에 **{voice}** 목소리를 사용할게요.", ephemeral=True
        )
    except (OSError, ValueError):
        LOGGER.exception("사용자 %s의 목소리 설정 저장에 실패했습니다.", interaction.user.id)
        await interaction.response.send_message(
            "목소리 설정을 저장하지 못했어요. 서버 로그를 확인해 주세요.", ephemeral=True
        )


@app_commands.command(name="tts", description="Supertonic 3로 글을 읽어 줍니다")
@app_commands.describe(text="읽을 내용")
async def tts_command(interaction: discord.Interaction, text: str) -> None:
    await _handle_tts(interaction, text)


@app_commands.command(name="말", description="Supertonic 3로 글을 읽어 줍니다")
@app_commands.describe(내용="읽을 내용")
async def speak_korean_command(interaction: discord.Interaction, 내용: str) -> None:
    await _handle_tts(interaction, 내용)


@app_commands.command(name="leave", description="재생을 중단하고 음성 채널에서 나갑니다")
async def leave_command(interaction: discord.Interaction) -> None:
    await _handle_leave(interaction)


@app_commands.command(name="퇴장", description="재생을 중단하고 음성 채널에서 나갑니다")
async def leave_korean_command(interaction: discord.Interaction) -> None:
    await _handle_leave(interaction)


VOICE_CHOICES = [
    app_commands.Choice(name=f"남성 {number} (M{number})", value=f"M{number}")
    for number in range(1, 6)
] + [
    app_commands.Choice(name=f"여성 {number} (F{number})", value=f"F{number}")
    for number in range(1, 6)
]


@app_commands.command(name="voice", description="내 TTS 목소리를 설정합니다")
@app_commands.describe(voice="사용할 Supertonic 3 목소리")
@app_commands.choices(voice=VOICE_CHOICES)
async def voice_command(
    interaction: discord.Interaction, voice: app_commands.Choice[str]
) -> None:
    await _handle_voice(interaction, voice.value)


@app_commands.command(name="목소리", description="내 TTS 목소리를 설정합니다")
@app_commands.describe(목소리="사용할 Supertonic 3 목소리")
@app_commands.choices(목소리=VOICE_CHOICES)
async def voice_korean_command(
    interaction: discord.Interaction, 목소리: app_commands.Choice[str]
) -> None:
    await _handle_voice(interaction, 목소리.value)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = Settings.from_env()
    DotoriBot(settings).run(settings.discord_token, log_handler=None)


if __name__ == "__main__":
    main()
