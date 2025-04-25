#!/usr/bin/env bash
set -euo pipefail

# Default interval (in seconds), configurable via YTDLP_POLL_INTERVAL_SECONDS
YTDLP_POLL_INTERVAL_SECONDS="${YTDLP_POLL_INTERVAL_SECONDS:-60}"

# Loop invoking the updater
while true; do
  echo "Running yt-dlp updater at $(date)..."
  /app/main.sh
  echo "Sleeping for $YTDLP_POLL_INTERVAL_SECONDS seconds..."
  sleep "$YTDLP_POLL_INTERVAL_SECONDS"
done