# social-style-radar

稳定版「AI 写真风格趋势雷达」：优先抓取 **TikTok + Instagram** 的公开网页信号，每天自动跑一次，输出可直接看的热门风格与可裁剪候选链接。

## 产出文件

- `styles_report.md`：中文趋势总结（Top 风格、证据链接、可裁剪效果图候选）
- `prompts.json`：风格到提示词模板（Midjourney + SDXL/Flux）
- `source_links.csv`：原始证据链接（platform, title, url, snippet, query）
- `style_images/`：按风格聚类的示例风格图（自动从证据页抓取 og:image，best-effort）
- `style_images_manifest.json`：风格图清单
- `state.json`：最近一次运行状态（时间、查询数、链接数、是否限流）
- `logs/`：每日运行日志与归档快照

## 手动运行

```bash
cd project/social-style-radar
python3 radar.py --once
```

## 输出到统一目录（给 style workflow 消费）

`run_daily.sh` 会把当日结果导出到：

- 默认：`/Users/yutingwang/.openclaw/workspace/data/style-daily/YYYY-MM-DD/social-style-radar/`
- 可通过环境变量覆盖：`STYLE_DAILY_ROOT=/your/path`

导出文件包括：
- `styles_report.md`
- `source_links.csv`
- `prompts.json`
- `state.json`
- `run_<timestamp>.log`

## 每天自动运行（macOS LaunchAgent）

1) 首次安装

```bash
cd project/social-style-radar
chmod +x run_daily.sh install_launchd.sh
./install_launchd.sh
```

2) 默认每天 `08:30` 运行（见 `com.openclaw.social-style-radar.plist`）

3) 检查任务状态

```bash
launchctl list | grep social-style-radar
```

4) 查看日志

```bash
tail -n 80 logs/launchd.out.log
tail -n 80 logs/launchd.err.log
```

## 稳定性设计

- TikTok/Instagram 查询优先，X/小红书仅补充。
- 内置重试 + 退避，降低临时网络波动影响。
- 遇到 429 限流会标注在报告中（best-effort，不会静默失败）。
- 每次运行自动归档结果到 `logs/`，方便回看和对比。

## Caveats

1. 不是平台官方热榜，只是公开网页信号代理指标。  
2. 搜索结果可能混入二级媒体/营销页面。  
3. 封闭内容和移动端原生内容覆盖有限。  
4. 若长期高频运行，建议接入官方搜索 API + key 池。  
