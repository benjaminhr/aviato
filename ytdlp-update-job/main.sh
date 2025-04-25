#!/usr/bin/env bash
set -euo pipefail

# Configuration
PYPI_API_URL="https://pypi.org/pypi/yt-dlp/json"
REQUIREMENTS_FILE="app/requirements.txt"
GIT_BRANCH="main"
WORKDIR="/workspace"
GITHUB_REPOSITORY="benjaminhr/aviato"
REPO_URL="https://github.com/$GITHUB_REPOSITORY.git"

# Ensure required environment variables are set
if [[ -z "${GITHUB_TOKEN-}" ]]; then
  echo "Error: GITHUB_TOKEN is not set." >&2
  exit 1
fi

# Clone or update the repository in the workspace
mkdir -p "$WORKDIR"
if [[ -d "$WORKDIR/.git" ]]; then
  echo "Fetching latest changes..."
  cd "$WORKDIR"
  git fetch origin
  git checkout "$GIT_BRANCH"
  git reset --hard "origin/$GIT_BRANCH"
else
  echo "Cloning repository..."
  git clone "$REPO_URL" "$WORKDIR"
  cd "$WORKDIR"
fi

# Fetch the latest yt-dlp version from PyPI
latest_version=$(curl -fsSL "$PYPI_API_URL" \
  | jq -r '
      .releases
    | to_entries
    | map({ version: .key, upload_time: (.value[0].upload_time_iso_8601) })
    | sort_by(.upload_time)
    | last
    | .version
  ')

# Read the current version from requirements.txt
current_version=$(grep -E '^yt-dlp>=' "$REQUIREMENTS_FILE" \
  | head -n1 \
  | sed -E 's|yt-dlp>=(.+)|\1|') || current_version=""

# Compare and update if necessary
if [[ "$latest_version" != "$current_version" ]]; then

  if [[ -n "${GIT_USER_EMAIL-}" && -n "${GIT_USER_NAME-}" ]]; then
    git config user.email "$GIT_USER_EMAIL"
    git config user.name "$GIT_USER_NAME"
  else
    echo "Warning: GIT_USER_EMAIL or GIT_USER_NAME not set; using default Git identity."
  fi
  echo "Updating yt-dlp from '$current_version' to '$latest_version'..."

  # Update requirements.txt line for yt-dlp
  sed -E "s|^yt-dlp>=.+|yt-dlp>=$latest_version|" "$REQUIREMENTS_FILE" > tmp && mv tmp "$REQUIREMENTS_FILE"

  git config user.email "ytdlp-updater@loop"
  git config user.name "YTDLP Updater"

  # Commit and push changes
  git add "$REQUIREMENTS_FILE"
  git commit -m "chore: bump yt-dlp to $latest_version"
  git push "https://${GITHUB_TOKEN}@github.com/$GITHUB_REPOSITORY.git" "$GIT_BRANCH"
  echo "Update committed and pushed."
else
  echo "No update needed: yt-dlp is already at '$current_version'."
fi