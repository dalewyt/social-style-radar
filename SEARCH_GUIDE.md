# Social Style Radar — TikTok 搜索指南

## 方案优先级

### ✅ 方案 A：Chrome Extension Relay（最优，真实帖子）

**适用场景**：日常 radar 运行，能拿到最新、最真实的 TikTok 内容

**步骤**：
1. 确认 Chrome 已登录 TikTok
2. 在 TikTok tab 上点 OpenClaw Browser Relay 扩展图标 → Attach Tab
3. 扩展配置：
   - Gateway URL: `http://127.0.0.1:18789`
   - Token: `c20e0ebd966567acf6120c93461306fc34080e8ca12b1ea5`
4. 使用 browser tool 搜索：

```python
# 搜索示例
browser(action="navigate", profile="chrome",
        url="https://www.tiktok.com/search?q=AI+portrait+video+style&t=1")
# 点 Videos 标签
browser(action="act", profile="chrome",
        request={"kind": "click", "ref": "Videos"})
# snapshot 抓结果
browser(action="snapshot", profile="chrome")
```

**推荐搜索词**（AI 人像视频方向）：
- `AI portrait video style`
- `AI video portrait trend`
- `ghibli AI portrait`
- `AI cinematic portrait`
- `AI live photo portrait`
- `AI caricature portrait`
- `AI barbie portrait`

---

### ✅ 方案 B：TikTok Creative Center（官方趋势数据）

**适用场景**：获取 trending hashtag 量化数据

**URL**：`https://ads.tiktok.com/business/creativecenter/trending-hashtags/pc/en`

**注意**：
- 未登录只能看全局热门 hashtag，无法按关键词过滤
- 登录后才能使用搜索框按 AI/portrait 等过滤
- 登录方式同方案 A（Chrome Relay）

---

### ⚠️ 方案 C：Brave Search API（Fallback）

**适用场景**：Chrome Relay 不可用时的备选

**限制**：
- 只能抓 TikTok discover 页面，无法拿到具体视频帖子
- `freshness` 过滤对 social post 效果差
- 结果偏 generic，不如真实搜索精准

**代码**（已在 `radar.py` 中实现）：
```python
brave_public_search(query, max_results=8)
# 使用 BRAVE_API_KEY 环境变量
# freshness 参数：pw=一周, pm=一月
```

---

## 建议的 Radar 工作流

1. **优先**：检查 Chrome Relay 是否可用（`browser(action=tabs, profile=chrome)`）
2. 可用 → 方案 A，搜 TikTok + Creative Center
3. 不可用 → 方案 C（Brave），同时飞书提醒用户 attach Chrome tab
4. 结果去重：`seen_urls.json`（14天窗口）
