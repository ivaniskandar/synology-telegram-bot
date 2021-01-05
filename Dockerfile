FROM jamiehewland/alpine-pypy:3.6-7.3.0-alpine3.11

# Prepare build dependencies
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    git \
    libc-dev \
    libffi-dev \
    openssl-dev \
    python3-dev

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade \
    python-telegram-bot \
    decorator \
    git+https://github.com/nicholaschum/synology-api@9e5d5190fa228985cc0d39136d1a58e3d6cfb930

# Delete build dependencies
RUN apk del .build-deps

# Install runtime dependencies
RUN apk add --no-cache --update \
    dumb-init \
    tzdata

ENV BOT_TOKEN=""
ENV BOT_OWNER_ID=""
ENV NAS_IP=""
ENV NAS_PORT=""
ENV DSM_ACCOUNT=""
ENV DSM_PASSWORD=""
ENV TZ="GMT"

COPY entrypoint.sh /entrypoint.sh
COPY syno_bot /syno_bot
ENTRYPOINT ["/entrypoint.sh"]
