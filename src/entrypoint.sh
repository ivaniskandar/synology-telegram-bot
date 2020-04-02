#!/bin/sh

# Checkers
if [[ -z "$BOT_TOKEN" ]]; then
    echo "BOT_TOKEN is not set"
    exit 1
fi
if [[ -z "$BOT_OWNER_ID" ]]; then
    echo "BOT_OWNER_ID is not set"
    exit 1
fi
if [[ -z "$NAS_IP" ]]; then
    echo "NAS_IP is not set"
    exit 1
fi
if [[ -z "$NAS_PORT" ]]; then
    echo "NAS_PORT is not set"
    exit 1
fi
if [[ -z "$DSM_ACCOUNT" ]]; then
    echo "DSM_ACCOUNT is not set"
    exit 1
fi
if [[ -z "$DSM_PASSWORD" ]]; then
    echo "DSM_PASSWORD is not set"
    exit 1
fi
# This value is optional
if [[ -z "$TORRENT_WATCH_LOCATION" ]]; then
    echo "TORRENT_WATCH_LOCATION is not set"
fi

# Write variables for bot
cat > /src/credentials.py << EOF
SYNOLOGY_NAS_BOT_TOKEN="${BOT_TOKEN}"
SYNOLOGY_NAS_BOT_OWNER="${BOT_OWNER_ID}"
SYNOLOGY_NAS_BOT_IP="${NAS_IP}"
SYNOLOGY_NAS_BOT_PORT="${NAS_PORT}"
SYNOLOGY_NAS_BOT_TORRENT_WATCH="${TORRENT_WATCH_LOCATION}"
SYNOLOGY_NAS_BOT_ACCOUNT="${DSM_ACCOUNT}"
SYNOLOGY_NAS_BOT_PASSWORD="${DSM_PASSWORD}"
EOF

echo "Finished preparations, starting..."
/usr/bin/dumb-init /usr/bin/python3 /src/bot.py
