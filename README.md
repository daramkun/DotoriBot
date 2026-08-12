# DotoriBot

다음 두 기능을 제공하는 Discord 봇입니다.

- `/tts` 또는 `/말`: 사용자가 들어가 있는 음성 채널에서 Supertonic 3로 텍스트를 읽습니다.
- `/leave` 또는 `/퇴장`: 재생 중인 음성과 대기열을 중단하고 음성 채널에서 나갑니다.
- 이모지만 하나 보낸 메시지: 원본을 지우고, 같은 표시 이름과 프로필 사진을 사용하는 웹훅으로 큰 이미지 파일을 다시 올립니다. Discord 커스텀 이모지(움직이는 이모지 포함)와 유니코드 이모지를 지원합니다.

Supertonic 3 추론은 봇이 실행되는 컴퓨터에서 로컬로 이루어집니다. 최초 실행 시 모델 약 400MB를 Hugging Face 캐시에 내려받습니다.

## 준비

1. Python 3.10 이상을 설치합니다. FFmpeg는 필요하지 않습니다.
2. Discord Developer Portal에서 애플리케이션과 Bot을 만듭니다.
3. **Bot → Privileged Gateway Intents → Message Content Intent**를 켭니다.
4. OAuth2 URL Generator에서 `bot`, `applications.commands` 범위를 선택하고 다음 권한으로 서버에 초대합니다.
   - View Channels / Send Messages / Attach Files
   - Manage Messages / Manage Webhooks
   - Connect / Speak
5. 설치하고 환경 파일을 만듭니다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
Copy-Item .env.example .env
```

`.env`의 `DISCORD_TOKEN`을 설정한 다음 실행합니다.

```powershell
python -m dotori_bot.bot
```

개발 중에는 `.env`의 `DEV_GUILD_ID`에 테스트 서버 ID를 넣는 편이 좋습니다. 서버 전용 명령은 즉시 반영되지만, 전역 슬래시 명령은 Discord에 나타나기까지 시간이 걸릴 수 있습니다.

## 설정

기본 음성은 `F1`, 언어는 한국어(`ko`)입니다. `.env`에서 `TTS_VOICE`, `TTS_LANGUAGE`, `TTS_SPEED`, `TTS_STEPS`를 바꿀 수 있습니다. 내장 음성은 `M1`-`M5`, `F1`-`F5`입니다.

여러 요청은 서버별 재생 대기열에 순서대로 들어갑니다. 마지막 재생 뒤 `VOICE_IDLE_SECONDS`가 지나면 봇이 음성 채널에서 자동으로 나갑니다.

## Docker

Dockerfile은 Python 패키지를 설치하는 `setup` 단계와 최소 실행 환경인 `runtime` 단계로 나뉩니다.

```powershell
docker build --target runtime -t dotoribot .
docker volume create dotoribot-cache
docker run --detach --name dotoribot --restart unless-stopped `
  --env-file .env `
  --mount source=dotoribot-cache,target=/home/dotoribot/.cache `
  dotoribot
```

캐시 볼륨에는 최초 실행 시 내려받는 Supertonic 3 모델이 보존됩니다. 볼륨을 연결하지 않아도 실행은 가능하지만 컨테이너를 새로 만들 때 모델을 다시 다운로드하게 됩니다.

## 참고 사항

- 이모지 재게시 웹훅은 해당 텍스트 채널에 처음 필요할 때 자동으로 생성됩니다.
- 유니코드 이모지 이미지는 Twemoji의 jsDelivr CDN에서 가져오므로 그 기능에는 인터넷 연결이 필요합니다. 커스텀 이모지는 Discord CDN에서 가져옵니다.
- 봇이 프로필과 표시 이름을 흉내 내는 것은 웹훅 표시 기능이며, 메시지에는 Discord의 `BOT` 표지가 붙습니다.
- Supertonic 모델에는 별도의 OpenRAIL-M 라이선스가 적용됩니다. 배포 전에 사용 조건을 확인하세요.

## 테스트

```powershell
python -m pip install -e ".[dev]"
pytest
```
