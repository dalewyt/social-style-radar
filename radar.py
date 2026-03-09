#!/usr/bin/env python3
"""
Social Style Radar — LLM-powered edition.

Flow:
  1. Brave Search: broad discovery queries on TikTok / Instagram / X
  2. Deduplicate & prioritize
  3. Gemini Flash: synthesize raw results into fresh style trends (JSON)
  4. Write report + prompts + state
"""

import argparse
import csv
import hashlib
import json
import os
import random
import re
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
OUT_CSV = BASE_DIR / "source_links.csv"
OUT_REPORT = BASE_DIR / "styles_report.md"
OUT_PROMPTS = BASE_DIR / "prompts.json"
STATE_FILE = BASE_DIR / "state.json"
SEEN_URLS_FILE = BASE_DIR / "seen_urls.json"
DEDUP_DAYS = 14
STYLE_IMAGES_DIR = BASE_DIR / "style_images"
STYLE_IMAGES_MANIFEST = BASE_DIR / "style_images_manifest.json"


@dataclass
class SearchResult:
    platform: str
    query: str
    title: str
    url: str
    snippet: str


# ──────────────────────────────────────────────
# HTTP helpers
# ──────────────────────────────────────────────

def fetch(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "ignore")


def clean_html(s: str) -> str:
    s = re.sub(r"<.*?>", "", s)
    for ent, ch in [("&amp;", "&"), ("&quot;", '"'), ("&#x27;", "'"),
                    ("&lt;", "<"), ("&gt;", ">")]:
        s = s.replace(ent, ch)
    return re.sub(r"\s+", " ", s).strip()


def normalize_url(url: str) -> str:
    p = urllib.parse.urlparse(url)
    return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/")


# ──────────────────────────────────────────────
# Search
# ──────────────────────────────────────────────

def brave_search(query: str, max_results: int = 10) -> List[Tuple[str, str, str]]:
    api_key = os.getenv("BRAVE_API_KEY", "").strip()
    if api_key:
        api_url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode(
            {"q": query, "count": max_results, "search_lang": "en", "country": "US"}
        )
        req = urllib.request.Request(
            api_url,
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": api_key,
                "User-Agent": "social-style-radar/2.0",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8", "ignore"))

        items, seen = [], set()
        for it in data.get("web", {}).get("results", [])[:max_results]:
            href = it.get("url", "")
            title = clean_html(it.get("title", "") or "")[:180]
            snippet = clean_html(it.get("description", "") or "")[:300]
            if not href or not title:
                continue
            key = normalize_url(href)
            if key in seen:
                continue
            seen.add(key)
            items.append((title, href, snippet))
        return items

    # Fallback: scrape Brave HTML SERP
    url = "https://search.brave.com/search?q=" + urllib.parse.quote(query) + "&source=web"
    html = fetch(url)
    anchors = re.findall(r'<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, re.S)
    items, seen = [], set()
    for href, inner in anchors:
        if any(d in href for d in ["search.brave.com", "cdn.search.brave.com",
                                    "imgs.search.brave.com", "tiles.search.brave.com"]):
            continue
        title_full = clean_html(inner)
        if len(title_full) < 8:
            continue
        key = normalize_url(href)
        if key in seen:
            continue
        seen.add(key)
        items.append((title_full[:180], href, title_full[:300]))
        if len(items) >= max_results:
            break
    return items


def search_with_retry(query: str, max_results: int = 10, retries: int = 3) -> Tuple[List[Tuple[str, str, str]], bool]:
    rate_limited = False
    for i in range(retries):
        try:
            return brave_search(query, max_results=max_results), rate_limited
        except Exception as e:
            if "429" in str(e).lower() or "too many" in str(e).lower():
                rate_limited = True
            if i < retries - 1:
                time.sleep(2 + i * 2 + random.random())
    return [], rate_limited


# ──────────────────────────────────────────────
# Dedup / prioritize
# ──────────────────────────────────────────────

def dedupe_results(results: List[SearchResult]) -> List[SearchResult]:
    seen, out = set(), []
    for r in results:
        key = normalize_url(r.url)
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def add_seed_fallback(rows: List[SearchResult]) -> List[SearchResult]:
    seeds = [
        SearchResult("tiktok", "seed", "AI Generated Image Trend | TikTok",
                     "https://www.tiktok.com/discover/ai-generated-image-trend?lang=en",
                     "ai generated image trend, photo trend, portrait"),
        SearchResult("tiktok", "seed", "AI Photo Style Trend | TikTok",
                     "https://www.tiktok.com/discover/ai-photo-style-trend",
                     "ai photo style, portrait filter, aesthetic"),
        SearchResult("instagram", "seed", "#aiportrait on Instagram",
                     "https://www.instagram.com/explore/tags/aiportrait/",
                     "aiportrait hashtag, professional headshot, portrait"),
        SearchResult("instagram", "seed", "#aiphoto on Instagram",
                     "https://www.instagram.com/explore/tags/aiphoto/",
                     "aiphoto trend, aesthetic, creative portrait"),
        SearchResult("x", "seed", "AI photo trend search | X",
                     "https://x.com/search?q=AI%20photo%20trend&src=typed_query",
                     "ai photo trend, cinematic, portrait"),
    ]
    existing = {normalize_url(r.url) for r in rows}
    for s in seeds:
        if normalize_url(s.url) not in existing:
            rows.append(s)
    return rows


def prioritize_rows(rows: List[SearchResult], max_total: int = 120) -> List[SearchResult]:
    grouped: Dict[str, List[SearchResult]] = defaultdict(list)
    for r in rows:
        grouped[r.platform].append(r)
    preferred = grouped.get("tiktok", []) + grouped.get("instagram", [])
    fallback = grouped.get("x", []) + grouped.get("xiaohongshu", [])
    out = preferred[: int(max_total * 0.8)]
    out.extend(fallback[: max_total - len(out)])
    if len(out) < max_total:
        out.extend([r for r in rows if r not in out][: max_total - len(out)])
    return out


# ──────────────────────────────────────────────
# Cross-day seen-URL tracking
# ──────────────────────────────────────────────

def load_seen_urls() -> dict:
    if SEEN_URLS_FILE.exists():
        try:
            return json.loads(SEEN_URLS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_seen_urls(seen: dict) -> None:
    cutoff = datetime.now(timezone.utc).timestamp() - DEDUP_DAYS * 86400
    pruned = {k: v for k, v in seen.items() if _parse_ts(v) > cutoff}
    SEEN_URLS_FILE.write_text(json.dumps(pruned, ensure_ascii=False, indent=2), encoding="utf-8")


def _parse_ts(iso: str) -> float:
    try:
        return datetime.fromisoformat(iso).timestamp()
    except Exception:
        return 0.0


def filter_new_urls(rows: List[SearchResult], seen: dict) -> Tuple[List[SearchResult], dict]:
    now = datetime.now(timezone.utc).isoformat()
    new_rows = []
    for r in rows:
        key = normalize_url(r.url)
        if key not in seen:
            new_rows.append(r)
            seen[key] = now
    return new_rows, seen


# ──────────────────────────────────────────────
# LLM synthesis (Gemini Flash)
# ──────────────────────────────────────────────

def _call_gemini(prompt: str, api_key: str, model: str = "gemini-2.0-flash") -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.75,
            "maxOutputTokens": 3000,
            "responseMimeType": "application/json",
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        data = json.loads(r.read().decode("utf-8", "ignore"))
    return data["candidates"][0]["content"]["parts"][0]["text"]


def synthesize_styles(rows: List[SearchResult]) -> Optional[List[dict]]:
    """
    Ask Gemini to read raw search results and synthesize trending AI photo styles.
    Returns a list of style dicts, or None on failure.
    """
    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or (os.getenv("GOOGLE_API_KEYS", "").split(",")[0].strip())
    )
    if not api_key:
        print("[LLM] No Gemini API key found, falling back to keyword mode.")
        return None

    # Build a compact context: title + URL + snippet for top rows
    context_lines = []
    for i, r in enumerate(rows[:100], 1):
        snippet = r.snippet[:200].replace("\n", " ")
        context_lines.append(f"{i}. [{r.platform.upper()}] {r.title}\n   {r.url}\n   {snippet}")
    context = "\n\n".join(context_lines)

    today = datetime.now().strftime("%Y-%m-%d")

    prompt = f"""你是专业社交媒体视觉风格分析师，专注 AI 生成图像与摄影风格趋势追踪。

今天是 {today}。以下是从 TikTok、Instagram、X 等平台今天搜索到的 {len(rows[:100])} 条原始内容（标题+链接+摘要）：

---
{context}
---

请根据以上内容，分析今天真实流行的 AI 照片/人像/写真风格趋势。

输出严格 JSON（不要有任何其他文字），格式如下：

{{
  "styles": [
    {{
      "name": "风格名称（中文，4-8字，要贴近今天实际内容，不要套用固定模板）",
      "description": "3-5个视觉特征词，顿号分隔，要具体真实",
      "trend_signal": "一句话说明为什么今天这个风格在trending（结合具体内容说）",
      "platforms": ["tiktok"],
      "confidence": 0.85,
      "reference_url": "必须从上方列表中选一个最具代表性的真实URL"
    }}
  ],
  "summary": "今天整体趋势的一句总结（中文）",
  "platform_counts": {{"tiktok": 0, "instagram": 0, "x": 0, "xiaohongshu": 0}}
}}

注意：
1. 识别 6-10 个**真正不同**的风格，不要强行凑数或重复
2. reference_url 必须原封不动来自上方列表，不能编造
3. 风格名称要反映今天实际搜到的内容，避免每天都写同样的6个固定风格
4. confidence 范围 0.5-0.99，根据证据多少决定
5. 按 confidence 从高到低排列
"""

    for attempt in range(3):
        try:
            raw = _call_gemini(prompt, api_key)
            # Strip possible markdown code fences
            raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
            raw = re.sub(r"\s*```$", "", raw.strip())
            data = json.loads(raw)
            styles = data.get("styles", [])
            if styles:
                print(f"[LLM] Gemini synthesized {len(styles)} styles.")
                return styles, data.get("summary", ""), data.get("platform_counts", {})
        except Exception as e:
            print(f"[LLM] Attempt {attempt + 1} failed: {e}")
            time.sleep(3)
    return None


# ──────────────────────────────────────────────
# Fallback: keyword-based scoring (no LLM)
# ──────────────────────────────────────────────

def score_styles_fallback(results: List[SearchResult]) -> Dict[str, Dict]:
    """Keyword-based fallback when LLM is unavailable."""
    clusters = {
        "AI证件照/职业头像": ["headshot", "linkedin", "professional", "证件照", "职业照", "头像", "id photo"],
        "复古胶片/电影感": ["film", "cinematic", "kodak", "vintage", "胶片", "电影感", "颗粒", "analog"],
        "吉卜力/动漫化肖像": ["ghibli", "anime", "cartoon", "吉卜力", "动漫", "studio ghibli"],
        "Y2K闪光自拍": ["y2k", "flash", "disposable", "千禧", "闪光", "ccd", "digicam", "2000s"],
        "AI年鉴/校园照": ["yearbook", "school photo", "年鉴", "校园照", "graduation"],
        "未来感3D/赛博人像": ["3d render", "cyberpunk", "futuristic", "neon", "赛博", "未来感", "sci-fi"],
        "柔光韩系人像": ["korean", "soft light", "韩系", "柔光", "清透", "玻璃皮", "kpop"],
        "极简商务头像": ["clean background", "corporate", "linkedin photo", "professional headshot", "商务"],
    }
    platform_weight = {"tiktok": 2.0, "instagram": 1.8, "x": 0.7, "xiaohongshu": 0.5}
    style_desc_fallback = {
        "AI证件照/职业头像": "干净布光、商务着装、平台头像化",
        "复古胶片/电影感": "颗粒感、低饱和、暖棕色调、35mm 叙事构图",
        "吉卜力/动漫化肖像": "柔和手绘质感、治愈配色、角色化人像",
        "Y2K闪光自拍": "强闪光、高反差、时间戳、千禧数码味",
        "AI年鉴/校园照": "90s-00s 校园棚拍、统一背景、怀旧证件感",
        "未来感3D/赛博人像": "霓虹边缘光、金属质感、都市夜景",
        "柔光韩系人像": "柔和光线、清透肤色、减龄感、韩式构图",
        "极简商务头像": "纯色背景、自然布光、干净画面、职场场景",
    }

    style_hits: Dict[str, List[SearchResult]] = {k: [] for k in clusters}
    for r in results:
        text = f"{r.title} {r.snippet}".lower()
        for style, kws in clusters.items():
            if any(kw.lower() in text for kw in kws):
                style_hits[style].append(r)

    scored: Dict[str, Dict] = {}
    for style, hits in style_hits.items():
        if not hits:
            continue
        uniq = {normalize_url(h.url): h for h in hits}
        uniq_hits = list(uniq.values())
        raw = sum(platform_weight.get(h.platform, 1.0) for h in uniq_hits)
        platforms = sorted({h.platform for h in uniq_hits})
        conf = min(0.95, 0.35 + 0.08 * len(uniq_hits) + 0.07 * len(platforms))
        ref_url = uniq_hits[0].url if uniq_hits else ""
        scored[style] = {
            "name": style,
            "description": style_desc_fallback.get(style, "基于近期高频内容"),
            "trend_signal": f"关键词命中 {len(uniq_hits)} 条链接",
            "platforms": platforms,
            "confidence": round(conf, 2),
            "reference_url": ref_url,
        }
    return dict(sorted(scored.items(), key=lambda kv: kv[1]["confidence"], reverse=True))


# ──────────────────────────────────────────────
# Report / output writers
# ──────────────────────────────────────────────

def write_report_llm(styles: List[dict], summary: str, total_rows: int,
                     platform_counts: dict, rate_limited: bool) -> None:
    lines = ["Social Style Radar｜AI Style Top 10（LLM 动态归纳）", ""]
    if summary:
        lines += [f"📊 今日趋势总结：{summary}", ""]

    for idx, s in enumerate(styles[:10], 1):
        name = s.get("name", "未知风格")
        desc = s.get("description", "")
        signal = s.get("trend_signal", "")
        ref = s.get("reference_url", "N/A")
        conf = s.get("confidence", 0)
        platforms = s.get("platforms", [])

        lines.append(f"{idx}) {name}：{desc}")
        if signal:
            lines.append(f"   趋势信号：{signal}")
        lines.append(f"   置信度：{conf:.0%}  平台：{', '.join(platforms)}")
        lines.append(f"- reference link: {ref}")
        lines.append("")

    # Platform distribution
    if not platform_counts:
        platform_counts = {}
    lines.append(f"样本量：去重后 {total_rows} 条链接；平台分布：{dict(platform_counts)}")
    if rate_limited:
        lines.append("注意：本轮出现搜索限流（429），结果为 best-effort。")

    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_report_fallback(scored: Dict[str, Dict], total_rows: int,
                           platform_counts: dict, rate_limited: bool) -> None:
    lines = ["Social Style Radar｜AI Style Top 10（关键词归类，LLM 不可用）", ""]
    for idx, (_, info) in enumerate(list(scored.items())[:10], 1):
        lines.append(f"{idx}) {info['name']}：{info['description']}")
        lines.append(f"   趋势信号：{info['trend_signal']}")
        lines.append(f"- reference link: {info.get('reference_url', 'N/A')}")
        lines.append("")
    lines.append(f"样本量：去重后 {total_rows} 条链接；平台分布：{dict(platform_counts)}")
    if rate_limited:
        lines.append("注意：本轮出现搜索限流（429），结果为 best-effort。")
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_csv(rows: List[SearchResult]) -> None:
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["platform", "title", "url", "snippet", "query"])
        for r in rows:
            w.writerow([r.platform, r.title, r.url, r.snippet, r.query])


def build_prompts(style_names: List[str]) -> Dict:
    out = {}
    for style in style_names:
        out[style] = {
            "midjourney": (
                f"portrait photo, {style} style, highly detailed skin texture, "
                "realistic lighting, editorial composition, 35mm lens --ar 3:4 --stylize 200"
            ),
            "sdxl_flux": (
                f"{style} style, photoreal portrait, cinematic light, subtle color grading, "
                "high detail, realistic skin, 35mm photography, "
                "negative prompt: lowres, blurry, distorted face"
            ),
        }
    return out


def save_state(query_count: int, link_count: int, rate_limited: bool, llm_used: bool) -> None:
    STATE_FILE.write_text(
        json.dumps(
            {
                "last_run_utc": datetime.now(timezone.utc).isoformat(),
                "query_count": query_count,
                "link_count": link_count,
                "rate_limited": rate_limited,
                "llm_used": llm_used,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


# ──────────────────────────────────────────────
# Style image export (unchanged utility)
# ──────────────────────────────────────────────

def _slugify(name: str) -> str:
    s = re.sub(r"[^\w\-\u4e00-\u9fff]+", "_", name.strip().lower())
    return re.sub(r"_+", "_", s).strip("_") or "style"


def _extract_og_image(page_url: str) -> str:
    try:
        html = fetch(page_url, timeout=20)
        m = re.search(
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I
        )
        if not m:
            m = re.search(
                r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I
            )
        return urllib.parse.urljoin(page_url, m.group(1).strip()) if m else ""
    except Exception:
        return ""


def _download_image(url: str, out_path: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            ct = (r.headers.get("Content-Type") or "").lower()
            if "image" not in ct:
                return False
            data = r.read()
        if len(data) < 1024:
            return False
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data)
        return True
    except Exception:
        return False


def export_style_images(style_names: List[str], rows: List[SearchResult], per_style: int = 4) -> None:
    STYLE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    manifest: Dict[str, List[str]] = {}
    url_index: Dict[str, SearchResult] = {normalize_url(r.url): r for r in rows}

    for style in style_names[:10]:
        slug = _slugify(style)
        style_dir = STYLE_IMAGES_DIR / slug
        style_dir.mkdir(parents=True, exist_ok=True)
        saved: List[str] = []
        seen_src: set = set()

        for r in rows:
            if len(saved) >= per_style:
                break
            src = r.url
            if src in seen_src:
                continue
            seen_src.add(src)
            img_url = _extract_og_image(src)
            if not img_url:
                continue
            ext = Path(urllib.parse.urlparse(img_url).path).suffix.lower()
            if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
                ext = ".jpg"
            fname = hashlib.sha1(img_url.encode()).hexdigest()[:12] + ext
            outp = style_dir / fname
            if outp.exists() or _download_image(img_url, outp):
                saved.append(str(outp.relative_to(BASE_DIR)))

        manifest[style] = saved

    STYLE_IMAGES_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ──────────────────────────────────────────────
# Main search query plan (discovery-oriented)
# ──────────────────────────────────────────────

QUERY_PLAN = {
    "tiktok": [
        # Broad AI photo discovery
        "site:tiktok.com AI photo trend 2025",
        "site:tiktok.com ai portrait filter trending",
        "site:tiktok.com ai photo aesthetic viral",
        "site:tiktok.com ai 写真 风格 trending",
        "site:tiktok.com ai 人像 滤镜 热门",
        # Specific style signals (kept broader)
        "site:tiktok.com ai generated photo challenge",
        "site:tiktok.com ai photo transformation viral",
        "site:tiktok.com cinematic portrait ai",
        "site:tiktok.com ai headshot trend",
        "site:tiktok.com ai anime portrait",
    ],
    "instagram": [
        "site:instagram.com AI portrait style trending 2025",
        "site:instagram.com ai photo filter aesthetic",
        "site:instagram.com ai photo transformation challenge",
        "site:instagram.com ai写真 风格 trend",
        "site:instagram.com ai人像 aesthetic viral",
        "site:instagram.com cinematic ai photo portrait",
        "site:instagram.com ai anime portrait style",
        "site:instagram.com ai headshot professional trending",
    ],
    "x": [
        "site:x.com AI photo trend style viral",
        "site:x.com AI 头像 风格 趋势 2025",
    ],
    "xiaohongshu": [
        "site:xiaohongshu.com AI 写真 风格 流行",
        "site:xiaohongshu.com AI 人像 滤镜 热门",
    ],
}


# ──────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────

def run() -> None:
    all_rows: List[SearchResult] = []
    rate_limited = False
    query_count = 0

    for platform, queries in QUERY_PLAN.items():
        for q in queries:
            query_count += 1
            items, limited = search_with_retry(q, max_results=8, retries=3)
            rate_limited = rate_limited or limited
            for title, url, snippet in items:
                all_rows.append(SearchResult(platform=platform, query=q,
                                             title=title, url=url, snippet=snippet))
            time.sleep(1.2 + random.random())

    all_rows = add_seed_fallback(all_rows)
    deduped = dedupe_results(all_rows)

    # Cross-day dedup
    seen_history = load_seen_urls()
    new_only, seen_history = filter_new_urls(deduped, seen_history)
    save_seen_urls(seen_history)
    prioritized = prioritize_rows(new_only if new_only else deduped)

    write_csv(prioritized)
    platform_counts = Counter([r.platform for r in prioritized])

    # ── LLM synthesis ──
    llm_result = synthesize_styles(prioritized)
    llm_used = llm_result is not None

    if llm_used:
        styles, summary, llm_platform_counts = llm_result
        # Merge platform counts (prefer our counted version)
        merged_counts = dict(platform_counts)
        write_report_llm(styles, summary, len(prioritized), merged_counts, rate_limited)
        style_names = [s.get("name", "") for s in styles]
    else:
        print("[INFO] Using keyword fallback.")
        scored = score_styles_fallback(prioritized)
        write_report_fallback(scored, len(prioritized), dict(platform_counts), rate_limited)
        style_names = list(scored.keys())

    prompts = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "llm_synthesis": llm_used,
        "styles": build_prompts(style_names[:10]),
    }
    OUT_PROMPTS.write_text(json.dumps(prompts, ensure_ascii=False, indent=2), encoding="utf-8")
    export_style_images(style_names, prioritized)
    save_state(query_count=query_count, link_count=len(prioritized),
               rate_limited=rate_limited, llm_used=llm_used)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.parse_args()
    run()
    print(f"✓ {OUT_REPORT}")
    print(f"✓ {OUT_CSV}")
    print(f"✓ {OUT_PROMPTS}")
    print(f"✓ {STATE_FILE}")
