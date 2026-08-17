# DotoriBot

다음 두 기능을 제공하는 Discord 봇입니다.

- `/tts` 또는 `/말`: 사용자가 들어가 있는 음성 채널에서 Supertonic 3로 텍스트를 읽습니다.
- `/leave` 또는 `/퇴장`: 재생 중인 음성과 대기열을 중단하고 음성 채널에서 나갑니다.
- `/voice` 또는 `/목소리`: `M1`-`M5`, `F1`-`F5` 중 내 TTS 목소리를 선택합니다. 선택은 재시작 후에도 유지됩니다.
- `/말시작`: 실행한 텍스트 채널에서 내가 보내는 일반 메시지를 자동으로 TTS 대기열에 추가합니다.
- `/말끝`: 내 채팅 메시지 자동 읽기를 중지합니다. 봇이 음성 채널에서 나가도 자동으로 중지됩니다.
- 서버 커스텀 이모지만 하나 보낸 메시지: 원본을 지우고, 같은 표시 이름과 프로필 사진을 사용하는 웹훅으로 큰 이미지 파일을 다시 올립니다. 정적·움직이는 서버 이모지를 지원하며 일반 유니코드 이모지는 처리하지 않습니다.

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

여러 요청은 서버별 재생 대기열에 순서대로 들어갑니다. 봇이 들어가 있는 음성 채널에서 일반 사용자가 모두 나가면 재생과 대기열을 정리하고 즉시 자동으로 나갑니다. 다른 봇만 남아 있는 경우에도 사람이 없는 것으로 처리합니다.

## Docker

Dockerfile은 Python 패키지를 설치하는 `setup` 단계와 최소 실행 환경인 `runtime` 단계로 나뉩니다.

```powershell
docker compose build
docker compose up --detach
```

캐시 볼륨에는 최초 실행 시 내려받는 Supertonic 3 모델이 보존되고, 데이터 볼륨에는 사용자별 목소리 설정이 저장됩니다.
Compose는 컨테이너를 `1000:1000` 사용자로 실행합니다. 기존에 생성된 볼륨의 소유자가 다른 경우에는 한 번만 다음 명령으로 보정하세요.

```powershell
docker compose run --rm --user 0 --entrypoint sh dotoribot -c "chown -R 1000:1000 /home/dotoribot/.cache /home/dotoribot/.data"
docker compose up --detach
```

## 참고 사항

- 이모지 재게시 웹훅은 해당 텍스트 채널에 처음 필요할 때 자동으로 생성됩니다.
- 서버 커스텀 이모지 이미지는 Discord CDN에서 가져옵니다.
- 봇이 프로필과 표시 이름을 흉내 내는 것은 웹훅 표시 기능이며, 메시지에는 Discord의 `BOT` 표지가 붙습니다.
- Supertonic 모델에는 별도의 OpenRAIL-M 라이선스가 적용됩니다. 배포 전에 사용 조건을 확인하세요.

## 테스트

```powershell
python -m pip install -e ".[dev]"
pytest
```
