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
  resultsDiv.innerHTML = '<div class="loading">🔍 搜索中... 正在分析热门风格</div>';
  
  try {
    const resp = await fetch('/api/search', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({query: query, category: currentCategory})
    });
    const data = await resp.json();
    
    let html = '';
    
    // 显示调试信息（可选展开）
    if (data.debug) {
      html += '<details style="margin-bottom:12px;"><summary style="cursor:pointer;color:#555;font-size:12px;padding:6px;">🔍 调试信息（查看实际搜索查询）</summary>';
      html += '<div style="background:#0d1430;padding:10px;border-radius:6px;margin-top:6px;font-size:11px;color:#7aa0e0;">';
      html += '<div><strong>用户查询：</strong>' + data.debug.user_query + '</div>';
      html += '<div><strong>分类：</strong>' + (data.debug.category || '全部') + '</div>';
      if (data.debug.search_queries) {
        html += '<div style="margin-top:6px;"><strong>实际搜索查询：</strong></div>';
        data.debug.search_queries.forEach((q, i) => {
          html += '<div style="margin-left:10px;color:#9fb0d1;">• ' + q + '</div>';
        });
      }
      html += '<div style="margin-top:6px;"><strong>找到结果：</strong>' + (data.debug.total_results || 0) + ' 条</div>';
      html += '</div></details>';
    }
    
    // 显示 LLM 提炼的具体风格
    if (data.styles && data.styles.length > 0) {
      html += '<div class="card" style="margin-bottom:20px;"><h3>✨ 发现的具体风格</h3><div class="results">';
      data.styles.forEach((s, i) => {
        html += `
          <div class="result-card" style="border-left:3px solid #4b7de0;">
            <div style="font-size:11px;color:#7aa0e0;margin-bottom:4px;">风格 ${i+1}</div>
            <div class="result-title" style="color:#6ea8fe;">${s.name}</div>
            <div class="result-snippet">${s.description}</div>
          </div>
        `;
      });
      html += '</div></div>';
    }
    
    // 显示原始搜索结果（折叠）
    if (data.results && data.results.length > 0) {
      html += '<details style="margin-top:20px;"><summary style="cursor:pointer;color:#7aa0e0;padding:10px;background:#121a31;border-radius:8px;">📋 查看原始搜索结果 (' + data.results.length + ' 条)</summary>';
      html += '<div class="results" style="margin-top:12px;">';
      data.results.forEach(r => {
        html += `
          <div class="result-card" style="opacity:0.8;">
            <div class="result-title" style="font-size:13px;">${r.title}</div>
            <div class="result-snippet" style="font-size:12px;">${r.snippet}</div>
            <div class="result-meta">
              <span class="tag">${r.platform}</span>
              ${r.category ? '<span class="tag">' + r.category + '</span>' : ''}
              <a href="${r.url}" target="_blank" style="color:#60a5fa;font-size:11px;">查看原文</a>
            </div>
          </div>
        `;
      });
      html += '</div></details>';
    }
    
    if (!html) {
      html = '<div class="card"><p style="color:#7aa0e0;">未找到相关结果</p></div>';
    }
    
    resultsDiv.innerHTML = html;
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
        
        # 构建搜索查询
        # 基础查询：用户关键词 + AI/风格相关词
        base_terms = [query, "AI", "style", "trend", "effect"]
        
        # 根据分类添加特定关键词
        if category != "all" and category in CATEGORIES:
            cat_info = CATEGORIES[category]
            # 只添加 1-2 个最相关的分类关键词
            base_terms.extend(cat_info['keywords'][:2])
        
        enhanced_query = " ".join(base_terms)
        
        # 搜索 TikTok 和 Instagram（分别构建查询）
        raw_results = []
        search_queries = []  # 记录实际查询，供调试
        
        for platform in ["tiktok", "instagram"]:
            # TikTok: 用 hashtag 和 trend 增强
            if platform == "tiktok":
                platform_query = f'site:tiktok.com "{query}" (AI OR filter OR effect) (trend OR viral OR popular)'
            else:
                platform_query = f'site:instagram.com "{query}" (AI OR filter OR style) (reels OR trending)'
            
            search_queries.append(platform_query)
            search_results = simple_brave_search(platform_query, max_results=8)
            
            for title, url, snippet in search_results:
                raw_results.append({
                    "platform": platform.capitalize(),
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                })
        
        if not raw_results:
            return jsonify({
                "results": [], 
                "styles": [],
                "debug": {
                    "user_query": query,
                    "search_queries": search_queries
                }
            })
        
        # 调用 Gemini 总结出具体风格（而非通用关键词）
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        styles = []
        
        if gemini_key and len(raw_results) >= 3:
            # 构建 LLM prompt
            snippets_text = "\n".join([
                f"[{i+1}] {r['title']}: {r['snippet'][:150]}"
                for i, r in enumerate(raw_results[:10])
            ])
            
            llm_prompt = f"""基于以下搜索结果，提炼出 3-5 个**具体的视觉风格特征**。

用户搜索：{query}
分类：{CATEGORIES.get(category, {}).get('name', '全部') if category != 'all' else '全部'}

搜索结果：
{snippets_text}

要求：
1. 提炼**具体的风格名称**（例如："黑白胶片质感证件照"、"复古港风写真"），而非通用词（❌"AI headshot"、❌"portrait style"）
2. 每个风格包含：风格名（5-10字）+ 视觉特征描述（20-40字）
3. 只输出 JSON 格式，无其他文字

输出格式：
[
  {{"name": "黑白胶片证件照", "description": "高对比度黑白色调，胶片颗粒质感，正式构图，职业氛围"}},
  {{"name": "复古港风写真", "description": "80年代港片色调，柔和光晕，复古妆容，怀旧滤镜效果"}}
]"""
            
            try:
                import urllib.request
                import json as json_lib
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": llm_prompt}]}],
                    "generationConfig": {"temperature": 0.3}
                }
                req = urllib.request.Request(
                    url,
                    data=json_lib.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                
                with urllib.request.urlopen(req, timeout=15) as resp:
                    llm_data = json_lib.loads(resp.read().decode("utf-8"))
                    text = (((llm_data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [{}])[0].get("text", "")
                    
                    # 解析 JSON
                    import re
                    json_match = re.search(r'\[.*\]', text, re.DOTALL)
                    if json_match:
                        styles = json_lib.loads(json_match.group(0))
            except Exception as e:
                print(f"Gemini summarization failed: {e}")
        
        # 关联原始结果到风格
        results_with_styles = []
        for r in raw_results[:10]:
            detected_cat = detect_category(f"{r['title']} {r['snippet']}")
            results_with_styles.append({
                "platform": r["platform"],
                "title": r["title"],
                "url": r["url"],
                "snippet": r["snippet"][:200] + "..." if len(r["snippet"]) > 200 else r["snippet"],
                "category": CATEGORIES.get(detected_cat, {}).get("name") if detected_cat else None,
            })
        
        return jsonify({
            "styles": styles,  # LLM 提炼的具体风格
            "results": results_with_styles,  # 原始搜索结果
            "debug": {
                "user_query": query,
                "category": category,
                "search_queries": search_queries,
                "total_results": len(raw_results)
            }
        })
    
    return app

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8898)
    args = parser.parse_args()
    
    app = create_app()
    app.run(host=args.host, port=args.port, debug=True)
