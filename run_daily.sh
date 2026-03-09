#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

set -a; source "/Users/yutingwang/.openclaw/workspace-daily-style/.env"; set +a
mkdir -p logs
TS="$(date +%F_%H-%M-%S)"
DAY="$(date +%F)"

python3 radar.py --once > "logs/run_${TS}.log" 2>&1
cp styles_report.md "logs/styles_report_${TS}.md"
cp source_links.csv "logs/source_links_${TS}.csv"
cp prompts.json "logs/prompts_${TS}.json"
cp state.json "logs/state_${TS}.json"
cp style_images_manifest.json "logs/style_images_manifest_${TS}.json" || true

# keep latest pointer
cp styles_report.md latest_styles_report.md
cp source_links.csv latest_source_links.csv
cp prompts.json latest_prompts.json

# export daily package for downstream style workflow
STYLE_DAILY_ROOT="${STYLE_DAILY_ROOT:-/Users/yutingwang/.openclaw/workspace/data/style-daily}"
OUT_DIR="${STYLE_DAILY_ROOT}/${DAY}/social-style-radar"
mkdir -p "$OUT_DIR"
cp styles_report.md "$OUT_DIR/styles_report.md"
cp source_links.csv "$OUT_DIR/source_links.csv"
cp prompts.json "$OUT_DIR/prompts.json"
cp state.json "$OUT_DIR/state.json"
cp style_images_manifest.json "$OUT_DIR/style_images_manifest.json" || true
if [ -d style_images ]; then
  rm -rf "$OUT_DIR/style_images"
  cp -R style_images "$OUT_DIR/style_images"
fi
cp "logs/run_${TS}.log" "$OUT_DIR/run_${TS}.log"

# send report to Telegram
if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
  python3 -c "
import json, os, urllib.request
token = os.environ['TELEGRAM_BOT_TOKEN']
chat_id = os.environ['TELEGRAM_CHAT_ID']
text = open('styles_report.md').read()[:4000]
msg = '📊 Style Radar Daily Report ($DAY)\n\n' + text
data = json.dumps({'chat_id': chat_id, 'text': msg}).encode()
req = urllib.request.Request(f'https://api.telegram.org/bot{token}/sendMessage', data=data, headers={'Content-Type': 'application/json'})
urllib.request.urlopen(req, timeout=60)
" && echo "Telegram sent" || echo "Telegram send failed"
fi

# send report to Feishu (with signature)
if [ -n "${FEISHU_WEBHOOK_URL:-}" ]; then
  FEISHU_TEXT="$(printf '📊 Style Radar Daily Report (%s)\n\n%s' "$DAY" "$(head -c 4000 styles_report.md)")"
  python3 -c "
import json, sys, time, hmac, hashlib, base64, urllib.request
text = sys.stdin.read()
webhook = '${FEISHU_WEBHOOK_URL}'
secret = '${FEISHU_BOT_SECRET:-}'
ts = str(int(time.time()))
payload = {'msg_type': 'text', 'content': {'text': text}}
if secret:
    sign_str = ts + '\n' + secret
    sign = base64.b64encode(hmac.new(sign_str.encode(), b'', hashlib.sha256).digest()).decode()
    payload['timestamp'] = ts
    payload['sign'] = sign
data = json.dumps(payload).encode()
req = urllib.request.Request(webhook, data=data, headers={'Content-Type': 'application/json'})
urllib.request.urlopen(req, timeout=60)
" <<< "$FEISHU_TEXT" 2>&1 && echo "Feishu sent" || echo "Feishu send failed"
fi

echo "Done at ${TS}"
echo "Exported to ${OUT_DIR}"