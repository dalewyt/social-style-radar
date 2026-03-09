#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_SRC="$DIR/com.openclaw.social-style-radar.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.openclaw.social-style-radar.plist"

cp "$PLIST_SRC" "$PLIST_DST"
launchctl unload "$PLIST_DST" >/dev/null 2>&1 || true
launchctl load "$PLIST_DST"
launchctl start com.openclaw.social-style-radar || true

echo "Installed + loaded: $PLIST_DST"
echo "Check status: launchctl list | grep social-style-radar"