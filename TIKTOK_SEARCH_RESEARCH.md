# TikTok 搜索工具 Research 报告（2026-03-09）

## 🎯 需求
搜索 TikTok 热门 AI 风格内容（hashtags、trends、viral videos）

---

## 📊 可用方案对比

### 1. ⭐ Apify TikTok Scraper（推荐）

**链接**: https://apify.com/clockworks/tiktok-scraper

**优点：**
- ✅ 专业级爬虫平台，维护良好
- ✅ 支持 URL、搜索查询、hashtags、profiles
- ✅ 云端运行，无需自维护
- ✅ 结构化 JSON 输出
- ✅ 反反爬虫能力强

**功能：**
- 搜索关键词/hashtags
- 提取视频元数据（likes, comments, shares, views）
- 获取作者信息
- 下载视频（可选）

**定价：**
- Free tier: $5 免费额度/月（约 100 次搜索）
- Pay as you go: $0.25 per 1000 results
- 月费计划: $49/月起

**Python 集成：**
```python
from apify_client import ApifyClient

client = ApifyClient(os.getenv("APIFY_API_KEY"))
run_input = {
    "searchQueries": ["AI portrait style"],
    "resultsPerPage": 20,
    "shouldDownloadVideos": False,
}
run = client.actor("clockworks/tiktok-scraper").call(run_input=run_input)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)
```

**评分：** ⭐⭐⭐⭐⭐ (5/5)

---

### 2. 🔥 ScrapeCreators TikTok API

**链接**: https://scrapecreators.com/tiktok-api

**优点：**
- ✅ 专注于 TikTok 数据
- ✅ RESTful API，易集成
- ✅ 实时数据，延迟低
- ✅ 支持搜索、trending、hashtags

**定价：**
- Starter: $19/月 (10,000 requests)
- Pro: $99/月 (100,000 requests)
- Enterprise: 自定义

**API 示例：**
```python
import requests

url = "https://api.scrapecreators.com/tiktok/search"
headers = {"Authorization": f"Bearer {API_KEY}"}
params = {"query": "AI photo style", "count": 20}
resp = requests.get(url, headers=headers, params=params)
data = resp.json()
```

**评分：** ⭐⭐⭐⭐ (4/5)

---

### 3. 💰 RapidAPI TikTok APIs

**链接**: https://rapidapi.com/search/tiktok

**热门选择：**
- **TikTok API23** by Lundehund
- **TikTok Services** by tiktok-api-development
- **TikTok Best Experience** by ponds4552

**优点：**
- ✅ 多个 API 可选
- ✅ RapidAPI 统一管理
- ✅ 相对便宜（$5-20/月）

**缺点：**
- ⚠️ 第三方维护，稳定性参差不齐
- ⚠️ 可能随时失效（TikTok 封禁）
- ⚠️ 数据质量不如 Apify/SerpAPI

**定价：**
- Basic: $5-10/月 (500-1000 requests)
- Pro: $20-30/月 (5000-10000 requests)

**评分：** ⭐⭐⭐ (3/5) - 性价比高但风险大

---

### 4. 🛠️ 自建爬虫（Python）

#### 选项 A：tiktok-scraper (Node.js/Python)
**GitHub**: https://github.com/drawrowfly/tiktok-scraper

**优点：**
- ✅ 免费开源
- ✅ 功能丰富（hashtag, trend, user, music）
- ✅ 活跃维护（11k+ stars）

**缺点：**
- ⚠️ 需要自己处理反反爬虫
- ⚠️ 可能被 TikTok 封 IP

**安装：**
```bash
npm i -g tiktok-scraper
# or
pip install tiktok-scraper
```

**使用：**
```bash
tiktok-scraper hashtag AI_portrait -n 50 --filepath ./output.json
```

**评分：** ⭐⭐⭐⭐ (4/5) - 适合技术团队

#### 选项 B：PyTok (Playwright-based)
**GitHub**: https://github.com/networkdynamics/pytok

**优点：**
- ✅ 基于 Playwright，模拟真实浏览器
- ✅ 反反爬虫能力强
- ✅ Python 原生

**缺点：**
- ⚠️ 速度较慢（浏览器渲染）
- ⚠️ 资源消耗大

**安装：**
```bash
pip install pytok
playwright install
```

**使用：**
```python
from pytok import TikTok

tt = TikTok()
videos = tt.search("AI portrait", count=50)
for v in videos:
    print(v['desc'], v['stats']['playCount'])
```

**评分：** ⭐⭐⭐ (3/5) - 稳定但慢

---

### 5. 🔍 SerpAPI TikTok Search

**链接**: https://serpapi.com/tiktok-search-api

**优点：**
- ✅ 企业级稳定性
- ✅ 无需处理反爬虫
- ✅ 多平台支持（TikTok, Instagram, YouTube）

**缺点：**
- 💰 较贵（$50/月起）

**定价：**
- Free: 100 searches/月
- Starter: $50/月 (5,000 searches)
- Pro: $150/月 (25,000 searches)

**API 示例：**
```python
from serpapi import GoogleSearch

params = {
    "engine": "tiktok",
    "keywords": "AI portrait style",
    "api_key": os.getenv("SERPAPI_KEY")
}
search = GoogleSearch(params)
results = search.get_dict()
for video in results.get("organic_results", []):
    print(video['title'], video['views'])
```

**评分：** ⭐⭐⭐⭐ (4/5) - 企业首选

---

### 6. 📡 Bright Data (Oxylabs)

**链接**: https://brightdata.com/products/web-scraper/tiktok

**优点：**
- ✅ 大规模数据采集能力
- ✅ 代理池 + 反检测
- ✅ 企业级 SLA

**缺点：**
- 💰💰 非常贵（$500+/月）
- ⚠️ 适合大规模需求

**评分：** ⭐⭐⭐ (3/5) - 仅适合企业

---

## 🎯 推荐方案（按需求）

### 🟢 最推荐：Apify TikTok Scraper

**适合：** 需要稳定、高质量数据，愿意支付合理费用

**成本：** $5-10/月（足够日常搜索 100-200 次）

**优势：**
- 云端运行，无需维护
- 反爬虫能力强
- 数据质量高
- 易集成

**集成步骤：**
1. 注册 Apify: https://apify.com/sign-up
2. 获取 API token
3. 安装 Python 客户端: `pip install apify-client`
4. 修改 `web.py` 添加 Apify 搜索函数

---

### 🟡 性价比：RapidAPI TikTok API

**适合：** 预算有限，可接受一定风险

**成本：** $5-20/月

**注意：** 选择评分高、更新频繁的 API

---

### 🔴 技术团队：自建爬虫 (tiktok-scraper)

**适合：** 有技术能力，想完全控制

**成本：** $0（代码免费）+ 服务器/代理成本

**风险：** 可能被封禁，需持续维护

---

## 📋 实施方案（Apify 集成示例）

### 修改 web.py

```python
# 添加 Apify 搜索函数
from apify_client import ApifyClient

def apify_tiktok_search(query: str, max_results: int = 20):
    """用 Apify 搜索 TikTok"""
    api_key = os.getenv("APIFY_API_KEY", "").strip()
    if not api_key:
        return []
    
    try:
        client = ApifyClient(api_key)
        run_input = {
            "searchQueries": [query],
            "resultsPerPage": max_results,
            "shouldDownloadVideos": False,
        }
        run = client.actor("clockworks/tiktok-scraper").call(run_input=run_input)
        
        results = []
        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            results.append({
                "title": item.get("text", ""),
                "url": item.get("webVideoUrl", ""),
                "snippet": item.get("text", "")[:200],
                "stats": {
                    "views": item.get("playCount", 0),
                    "likes": item.get("diggCount", 0),
                    "shares": item.get("shareCount", 0),
                }
            })
        return results
    except Exception as e:
        print(f"Apify search failed: {e}")
        return []

# 在 api_search 中使用
@app.route("/api/search", methods=["POST"])
def api_search():
    # ... 现有代码 ...
    
    # 优先用 Apify，fallback 到 Brave
    apify_results = apify_tiktok_search(query, max_results=10)
    if apify_results:
        raw_results.extend([
            {"platform": "TikTok", "title": r["title"], "url": r["url"], "snippet": r["snippet"]}
            for r in apify_results
        ])
    else:
        # fallback 到 Brave Search
        ...
```

### 环境变量
```bash
APIFY_API_KEY=your_apify_api_key
```

---

## 💰 成本对比（每月搜索 200 次）

| 方案 | 月费 | 效果 | 维护成本 |
|---|---|---|---|
| **Apify** | $5-10 | ⭐⭐⭐⭐⭐ | 无 |
| **ScrapeCreators** | $19 | ⭐⭐⭐⭐ | 无 |
| **RapidAPI** | $5-10 | ⭐⭐⭐ | 无 |
| **SerpAPI** | $50 | ⭐⭐⭐⭐ | 无 |
| **自建爬虫** | $0-20 | ⭐⭐⭐ | 高 |
| **Brave Search**（当前） | $0 | ⭐⭐⭐ | 无 |

---

## ✅ 下一步建议

1. **短期（本周）**: 继续优化 Brave Search 查询
2. **中期（下周）**: 试用 Apify 免费额度（$5），评估效果
3. **长期（下月）**: 如果 Apify 效果好，升级到付费计划

---

**最后更新**: 2026-03-09  
**研究者**: OpenClaw Assistant
