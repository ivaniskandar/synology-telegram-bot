FROM alpine:3.11.5

# Prepare dependencies
RUN apk update && apk add \
    dumb-init \
    git \
    python3 \
    py3-pip

RUN apk add py3-telegram-bot --update-cache --repository http://dl-cdn.alpinelinux.org/alpine/edge/testing/ --allow-untrusted

# Tidy up apk cache
RUN rm -rf /var/cache/apk/*

# Install Python dependencies
RUN pip3 install --upgrade \
    pip \
    decorator \
    git+https://github.com/nicholaschum/synology-api

ENV BOT_TOKEN=""
ENV BOT_OWNER_ID=""
ENV NAS_IP=""
ENV NAS_PORT=""
ENV TORRENT_WATCH_LOCATION=""
ENV DSM_ACCOUNT=""
ENV DSM_PASSWORD=""

COPY src /src
WORKDIR /src
ENTRYPOINT ["/src/entrypoint.sh"]
