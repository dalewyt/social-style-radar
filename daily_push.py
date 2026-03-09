#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import subprocess
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPORT = BASE_DIR / "styles_report.md"


def feishu_sign(secret: str) -> tuple[str, str]:
    ts = str(int(time.time()))
    to_sign = f"{ts}\n{secret}".encode("utf-8")
    sign = base64.b64encode(hmac.new(to_sign, digestmod=hashlib.sha256).digest()).decode("utf-8")
    return ts, sign


def send_feishu(webhook: str, text: str, secret: str = "") -> str:
    payload: dict = {"msg_type": "text", "content": {"text": text}}
    if secret:
        ts, sign = feishu_sign(secret)
        payload["timestamp"] = ts
        payload["sign"] = sign

    req = urllib.request.Request(
        webhook,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "ignore")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--run-radar", action="store_true", help="run radar.py --once before sending")
    p.add_argument("--webhook", required=True)
    p.add_argument("--secret", default="")
    args = p.parse_args()

    if args.run_radar:
        subprocess.check_call(["python3", "radar.py", "--once"], cwd=str(BASE_DIR))

    if not REPORT.exists():
        raise SystemExit(f"report not found: {REPORT}")

    text = REPORT.read_text(encoding="utf-8").strip()
    if len(text) > 3500:
        text = text[:3500] + "\n\n(报告过长，已截断)"

    resp = send_feishu(args.webhook, text, args.secret)
    print(resp)


if __name__ == "__main__":
    main()
