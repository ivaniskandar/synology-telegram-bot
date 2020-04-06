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
    git+https://github.com/nicholaschum/synology-api@Improving-code

# Delete build dependencies
RUN apk del .build-deps

# Install runtime dependencies
RUN apk add --no-cache \
    dumb-init

ENV BOT_TOKEN=""
ENV BOT_OWNER_ID=""
ENV NAS_IP=""
ENV NAS_PORT=""
ENV TORRENT_WATCH_LOCATION=""
ENV DSM_ACCOUNT=""
ENV DSM_PASSWORD=""

COPY entrypoint.sh /entrypoint.sh
COPY syno_bot /syno_bot
ENTRYPOINT ["/entrypoint.sh"]
