#!/usr/bin/env python3
"""
Social Style Radar Web UI
允许用户输入想要的风格/玩法，实时搜索热门 style
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from categories import CATEGORIES, detect_category

BASE_DIR = Path(__file__).resolve().parent

# 简化的搜索函数（避免导入 radar.py 的复杂依赖）
def simple_brave_search(query: str, max_results: int = 10):
    """简化版 Brave 搜索"""
    import urllib.request
    import urllib.parse
    import json as json_lib
    
    api_key = os.getenv("BRAVE_API_KEY", "").strip()
    if not api_key:
        return []
    
    try:
        url = f"https://api.search.brave.com/res/v1/web/search?q={urllib.parse.quote(query)}&count={max_results}"
        req = urllib.request.Request(url, headers={"X-Subscription-Token": api_key})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json_lib.loads(resp.read().decode("utf-8"))
            results = []
            for item in data.get("web", {}).get("results", []):
                title = item.get("title", "")
                url = item.get("url", "")
                snippet = item.get("description", "")
                results.append((title, url, snippet))
            return results
    except Exception:
        return []

HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Social Style Radar - Search</title>
  <style>
    :root { --bg:#0b1020; --card:#121a31; --muted:#9fb0d1; --text:#ecf2ff; --accent:#6ea8fe; }
    * { box-sizing: border-box; }
    body { margin:0; font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; background: linear-gradient(180deg,#070b16,#0f1730); color:var(--text); padding:20px; }
    .container { max-width: 1200px; margin: 0 auto; }
    .card { background: rgba(18,26,49,.92); border: 1px solid rgba(120,160,255,.18); border-radius: 14px; padding: 20px; margin-bottom: 20px; }
    h1 { margin-top: 0; }
    input, select, button { border-radius: 10px; border:1px solid #2a3d73; background:#0f1730; color:#eaf1ff; padding:12px; font-size:14px; }
    button { cursor:pointer; background: linear-gradient(180deg,#5f97ff,#4b7de0); border:none; font-weight:600; }
    .search-form { display: flex; gap: 12px; margin-bottom: 20px; }
    .search-form input { flex: 1; }
    .categories { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px; }
    .cat-btn { padding: 8px 16px; border-radius: 20px; background: #1e3a8a; color: #c8d8ff; border: 1px solid #3b7de0; cursor: pointer; font-size: 13px; }
    .cat-btn.active { background: #4b7de0; color: #fff; font-weight: 600; }
    .cat-btn:hover { border-color: #60a5fa; }
    .results { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
    .result-card { background: #0d1430; border: 1px solid #263b71; border-radius: 12px; padding: 16px; }
    .result-title { font-weight: 600; margin-bottom: 8px; color: #c8d8ff; }
    .result-snippet { font-size: 13px; color: #7aa0e0; line-height: 1.5; margin-bottom: 8px; }
    .result-meta { font-size: 12px; color: #555; }
    .loading { text-align: center; padding: 40px; color: #7aa0e0; }
    .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; background: #1e3a8a; color: #c8d8ff; margin-right: 6px; }
  </style>
</head>
<body>
<div class="container">
  <div class="card">
    <h1>🔍 Social Style Radar</h1>
    <p style="color:#7aa0e0;">实时搜索 TikTok/Instagram 热门风格，按玩法分类</p>
    
    <div class="categories" id="categories">
      <div class="cat-btn active" data-cat="all" onclick="selectCategory('all')">🌐 全部</div>
      {% for cat_id, cat in categories.items() %}
      <div class="cat-btn" data-cat="{{ cat_id }}" onclick="selectCategory('{{ cat_id }}')">
        {{ cat['name'] }} <span class="tag">{{ cat['priority'] }}</span>
      </div>
      {% endfor %}
    </div>
    
    <div class="search-form">
      <input type="text" id="query" placeholder="输入风格关键词，例如：证件照、电影感、复古......" />
      <button onclick="doSearch()">搜索</button>
    </div>
  </div>
  
  <div id="results"></div>
</div>

<script>
let currentCategory = 'all';

function selectCategory(cat) {
  currentCategory = cat;
  document.querySelectorAll('.cat-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.cat === cat);
  });
}

async function doSearch() {
  const query = document.getElementById('query').value.trim();
  if (!query) { alert('请输入搜索关键词'); return; }
  
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = '<div class="loading">搜索中...</div>';
  
  try {
    const resp = await fetch('/api/search', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({query: query, category: currentCategory})
    });
    const data = await resp.json();
    
    if (data.results && data.results.length > 0) {
      resultsDiv.innerHTML = '<div class="results">' + data.results.map(r => `
        <div class="result-card">
          <div class="result-title">${r.title}</div>
          <div class="result-snippet">${r.snippet}</div>
          <div class="result-meta">
            <span class="tag">${r.platform}</span>
            ${r.category ? '<span class="tag">' + r.category + '</span>' : ''}
            <a href="${r.url}" target="_blank" style="color:#60a5fa;font-size:12px;">查看原文</a>
          </div>
        </div>
      `).join('') + '</div>';
    } else {
      resultsDiv.innerHTML = '<div class="card"><p style="color:#7aa0e0;">未找到相关结果</p></div>';
    }
  } catch (e) {
    resultsDiv.innerHTML = '<div class="card"><p style="color:#ff9a9a;">搜索失败: ' + e.message + '</p></div>';
  }
}

// Enter 键触发搜索
document.getElementById('query').addEventListener('keypress', e => {
  if (e.key === 'Enter') doSearch();
});
</script>
</body>
</html>
"""

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SESSION_SECRET", "change-me-in-prod")
    
    # 密码保护
    APP_PASSWORD = os.getenv("APP_PASSWORD", "").strip()
    
    from flask import session, redirect, url_for
    
    @app.before_request
    def require_auth():
        if not APP_PASSWORD:
            return None  # 无密码模式
        if request.path in {"/login", "/healthz"}:
            return None
        if session.get("authed") is True:
            return None
        return redirect(url_for("login", next=request.full_path if request.query_string else request.path))
    
    @app.route("/healthz")
    def healthz():
        return {"ok": True}
    
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if not APP_PASSWORD:
            return redirect(url_for("home"))
        
        if request.method == "POST":
            pwd = request.form.get("password", "")
            nxt = request.form.get("next", "/")
            if pwd == APP_PASSWORD:
                session["authed"] = True
                return redirect(nxt or "/")
            return render_template_string("""
                <html><body style='font-family:sans-serif;text-align:center;padding:100px;'>
                <h2>🔒 Social Style Radar</h2>
                <form method='post'>
                <input type='hidden' name='next' value='{{ nxt }}' />
                <input type='password' name='password' placeholder='Password' style='padding:10px;font-size:16px;' required /><br><br>
                <button type='submit' style='padding:10px 20px;font-size:16px;'>Login</button>
                <p style='color:red;'>密码错误</p>
                </form></body></html>
            """, nxt=nxt)
        
        nxt = request.args.get("next", "/")
        return render_template_string("""
            <html><body style='font-family:sans-serif;text-align:center;padding:100px;'>
            <h2>🔒 Social Style Radar</h2>
            <form method='post'>
            <input type='hidden' name='next' value='{{ nxt }}' />
            <input type='password' name='password' placeholder='Password' style='padding:10px;font-size:16px;' required /><br><br>
            <button type='submit' style='padding:10px 20px;font-size:16px;'>Login</button>
            </form></body></html>
        """, nxt=nxt)
    
    @app.route("/")
    def home():
        return render_template_string(HTML_TEMPLATE, categories=CATEGORIES)
    
    @app.route("/api/search", methods=["POST"])
    def api_search():
        data = request.get_json()
        query = data.get("query", "").strip()
        category = data.get("category", "all")
        
        if not query:
            return jsonify({"error": "missing query"}), 400
        
        # 构建搜索查询（根据分类添加关键词）
        if category != "all" and category in CATEGORIES:
            cat_info = CATEGORIES[category]
            # 添加分类关键词增强搜索
            enhanced_query = f"{query} {' OR '.join(cat_info['keywords'][:3])}"
        else:
            enhanced_query = query
        
        # 搜索 TikTok 和 Instagram
        results = []
        for platform in ["tiktok", "instagram"]:
            platform_query = f"site:{platform}.com {enhanced_query} AI photo style"
            raw_results = simple_brave_search(platform_query, max_results=5)
            
            for title, url, snippet in raw_results:
                # 简单分类（基于关键词匹配）
                detected_cat = None
                snippet_lower = f"{title} {snippet}".lower()
                for cat_id, cat_info in CATEGORIES.items():
                    if any(kw.lower() in snippet_lower for kw in cat_info["keywords"]):
                        detected_cat = cat_info["name"]
                        break
                
                results.append({
                    "platform": platform.capitalize(),
                    "title": title,
                    "url": url,
                    "snippet": snippet[:200] + "..." if len(snippet) > 200 else snippet,
                    "category": detected_cat,
                })
        
        return jsonify({"results": results})
    
    return app

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8898)
    args = parser.parse_args()
    
    app = create_app()
    app.run(host=args.host, port=args.port, debug=True)
