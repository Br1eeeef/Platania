#!/usr/bin/env bash
set -Eeuo pipefail

exec 9>/run/lock/platania-deploy.lock
flock -n 9 || exit 0

APP_ROOT=/opt/platania
REPOSITORY="$APP_ROOT/repository"
RELEASES="$APP_ROOT/releases"
CURRENT="$APP_ROOT/current"
VENV="$APP_ROOT/venv"
LOG_PREFIX="[platania-deploy]"

cd "$REPOSITORY"
git fetch --quiet origin main
TARGET_SHA=$(git rev-parse origin/main)
CURRENT_SHA=$(cat "$CURRENT/.release-sha" 2>/dev/null || true)
if [[ "$TARGET_SHA" == "$CURRENT_SHA" ]]; then
  echo "$LOG_PREFIX already current $TARGET_SHA"
  exit 0
fi

STAMP=$(date -u +%Y%m%d%H%M%S)
RELEASE="$RELEASES/$STAMP-${TARGET_SHA:0:8}"
mkdir -p "$RELEASES" "$RELEASE"
git archive "$TARGET_SHA" | tar -x -C "$RELEASE"
rm -rf -- "$RELEASE/data"
ln -sfn "$APP_ROOT/shared/data" "$RELEASE/data"

REQ_HASH=$(sha256sum "$RELEASE/api/requirements.txt" | awk '{print $1}')
OLD_REQ_HASH=$(cat "$APP_ROOT/.requirements.sha256" 2>/dev/null || true)
if [[ ! -x "$VENV/bin/python" ]]; then
  python3 -m venv "$VENV"
fi
if [[ "$REQ_HASH" != "$OLD_REQ_HASH" ]]; then
  "$VENV/bin/pip" install --no-cache-dir -r "$RELEASE/api/requirements.txt"
  echo "$REQ_HASH" > "$APP_ROOT/.requirements.sha256"
fi

cd "$RELEASE/web"
export NODE_OPTIONS=--max-old-space-size=512
pnpm install --frozen-lockfile --prod=false --store-dir "$APP_ROOT/pnpm-store"
pnpm build
echo "$TARGET_SHA" > "$RELEASE/.release-sha"

PREVIOUS=$(readlink -f "$CURRENT" 2>/dev/null || true)
ln -sfn "$RELEASE" "$APP_ROOT/current.next"
mv -Tf "$APP_ROOT/current.next" "$CURRENT"
systemctl restart platania-api.service

for _ in {1..15}; do
  if curl --fail --silent --max-time 3 http://127.0.0.1:8010/api/health >/dev/null; then
    find "$RELEASES" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' | sort -nr | tail -n +6 | cut -d' ' -f2- | xargs -r rm -rf --
    echo "$LOG_PREFIX deployed $TARGET_SHA"
    exit 0
  fi
  sleep 2
done

echo "$LOG_PREFIX health check failed; rolling back" >&2
if [[ -n "$PREVIOUS" && -d "$PREVIOUS" ]]; then
  ln -sfn "$PREVIOUS" "$APP_ROOT/current.next"
  mv -Tf "$APP_ROOT/current.next" "$CURRENT"
  systemctl restart platania-api.service
fi
exit 1
