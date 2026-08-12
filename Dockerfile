# syntax=docker/dockerfile:1

# SETUP: Python 의존성을 독립된 가상환경에 설치한다.
FROM python:3.12-slim AS setup

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /build

RUN python -m venv "$VIRTUAL_ENV"

COPY pyproject.toml README.md ./
COPY dotori_bot ./dotori_bot

RUN python -m pip install --upgrade pip setuptools wheel \
    && python -m pip install . \
    && python -m pip check


# RUNTIME: 실행에 필요한 가상환경과 네이티브 라이브러리만 포함한다.
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    XDG_CACHE_HOME=/home/dotoribot/.cache

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        ca-certificates \
        libgomp1 \
        libopus0 \
        libsndfile1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin dotoribot \
    && mkdir -p /home/dotoribot/.cache \
    && chown -R dotoribot:dotoribot /home/dotoribot

COPY --from=setup /opt/venv /opt/venv

USER dotoribot
WORKDIR /home/dotoribot

# Supertonic 3 모델은 첫 TTS 요청 때 ~/.cache/supertonic3에 다운로드된다.
# 캐시 유지를 위해 실행 시 /home/dotoribot/.cache를 볼륨으로 마운트하는 것을 권장한다.
VOLUME ["/home/dotoribot/.cache"]

ENTRYPOINT ["python", "-m", "dotori_bot.bot"]
