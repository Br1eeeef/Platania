#!/usr/bin/env bash
set -Eeuo pipefail

SWAP_FILE=/swapfile-platania
if swapon --show=NAME --noheadings | grep -qx "$SWAP_FILE"; then
  exit 0
fi
if [[ -e "$SWAP_FILE" ]]; then
  echo "Refusing to overwrite existing $SWAP_FILE" >&2
  exit 1
fi
fallocate -l 2G "$SWAP_FILE"
chmod 600 "$SWAP_FILE"
mkswap "$SWAP_FILE"
swapon "$SWAP_FILE"
echo "$SWAP_FILE none swap sw 0 0" >> /etc/fstab

