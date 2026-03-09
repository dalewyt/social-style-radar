# Social Style Radar 升级指南

## 🆕 新功能

### 1. 玩法分类（Categories）
现在风格会按以下分类组织：
- **[P0] AI Photo**: 完全不同的风格化照片，保持人物一致性
- **[P0] Couple Photo**: 双人合影风格化
- **[P0] AI Video**: 视频风格化/转场/特效
- **[P1] AI Edit**: 基于原片增加效果（滤镜/调色）

### 2. 历史去重（Style Deduplication）
- 避免 14 天内重复推荐相同风格
- 基于风格关键词的语义相似度去重
- 自动记录每日推荐风格到 `style_history.json`

### 3. Web 搜索界面
- 实时搜索 TikTok/Instagram 热门风格
- 按玩法分类筛选
- 支持自定义搜索关键词

---

## 📦 文件结构

```
social-style-radar/
├── categories.py           # 玩法分类定义
├── style_dedup.py          # 风格去重逻辑
├── style_history.json      # 历史风格记录（自动生成）
├── web.py                  # Web 搜索界面
├── radar.py                # 核心爬虫（待升级）
└── UPGRADE_GUIDE.md        # 本文件
```

---

## 🚀 使用方法

### 启动 Web 搜索界面

```bash
cd ~/.openclaw/workspace-daily-style/agents/daily_style/social-style-radar
python3 web.py --host 0.0.0.0 --port 8898
```

访问：http://localhost:8898

**功能：**
- 选择玩法分类（AI Photo / Couple Photo / AI Edit / AI Video）
- 输入风格关键词（例如：证件照、电影感、复古）
- 实时搜索并显示结果

---

## 🔧 集成到 radar.py

### 修改步骤（待实现）

1. **导入分类模块**
```python
from categories import CATEGORIES, detect_category, get_all_search_queries
from style_dedup import filter_duplicate_styles, record_today_styles
```

2. **扩展搜索查询**
```python
# 原有通用查询
general_queries = [...]

# 添加分类特定查询
category_queries = get_all_search_queries()

# 合并
all_queries = general_queries + category_queries
```

3. **风格分类检测**
```python
for style in llm_styles:
    # 自动检测分类
    category = detect_category(f"{style['name']} {style['description']}")
    style["category"] = category
```

4. **历史去重**
```python
# LLM 生成风格后
llm_styles = parse_llm_output(...)

# 过滤重复风格
filtered_styles = filter_duplicate_styles(llm_styles, threshold=0.6)

# 记录今日风格
record_today_styles(filtered_styles)
```

5. **报告输出格式更新**
```python
# 在 write_report_llm 中添加分类信息
lines.append(f"   分类：{s.get('category', 'N/A')}")
```

---

## 🎯 预期效果

### Before（旧版）
```
1) 证件照：专业正式的人像照片风格
   趋势信号：关键词命中 12 条链接
   置信度：85%  平台：tiktok, instagram
```

### After（新版）
```
1) 证件照：专业正式的人像照片风格
   分类：AI Photo [P0]
   趋势信号：关键词命中 12 条链接
   置信度：85%  平台：tiktok, instagram
   （已过滤重复：该风格在过去 7 天内未出现）
```

---

## 📊 配置参数

### 去重阈值调整

编辑 `style_dedup.py`：
```python
DEDUP_DAYS = 14  # 历史去重天数（默认14天）

# 调用时指定相似度阈值
filtered = filter_duplicate_styles(styles, threshold=0.6)
# threshold 范围: 0.0 (完全不去重) - 1.0 (完全相同才去重)
# 推荐值: 0.5-0.7
```

### 分类关键词扩展

编辑 `categories.py`：
```python
CATEGORIES = {
    "ai_photo": {
        "keywords": ["portrait", "headshot", "证件照", ...],  # 添加更多关键词
        "search_queries": [...]  # 添加更多搜索查询
    }
}
```

---

## 🔗 部署到 Railway/Render

### 环境变量
```bash
BRAVE_API_KEY=your_brave_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### Procfile（web 模式）
```
web: python3 web.py --host 0.0.0.0 --port $PORT
```

### Procfile（定时任务模式）
```
worker: python3 radar.py --once && python3 daily_push.py
```

---

## 🐛 故障排查

### Web 界面搜索失败
- 检查 `BRAVE_API_KEY` 环境变量
- 确认 API 配额未用尽

### 风格一直重复
- 检查 `style_history.json` 是否正常生成
- 调低 `threshold` 参数（例如从 0.6 降到 0.5）

### 分类检测不准
- 扩展 `categories.py` 中的关键词列表
- 检查 `detect_category` 逻辑

---

## 📝 TODO

- [ ] 修改 `radar.py` 集成分类和去重逻辑
- [ ] 添加玩法分类到 Feishu 推送格式
- [ ] Web 界面支持手动标记风格分类
- [ ] 支持多语言（英文/中文）风格名称
- [ ] 添加风格热度趋势图表

---

**最后更新：** 2026-03-09  
**版本：** v2.0-beta
