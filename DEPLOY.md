# Social Style Radar - Render 部署指南

## 🚀 一键部署到 Render

### 方法1：通过 GitHub（推荐）

1. **推送代码到 GitHub**
   ```bash
   cd ~/.openclaw/workspace-daily-style/agents/daily_style/social-style-radar
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/social-style-radar.git
   git push -u origin main
   ```

2. **连接 Render**
   - 访问 https://dashboard.render.com
   - 点击 **New** → **Web Service**
   - 连接你的 GitHub 仓库
   - 选择 `social-style-radar` 仓库
   - Render 会自动检测 `render.yaml` 配置

3. **配置环境变量**
   在 Render Dashboard → Environment 添加：
   
   | Key | Value | 说明 |
   |-----|-------|------|
   | `BRAVE_API_KEY` | `your_brave_api_key` | 必填 - Brave Search API Key |
   | `APP_PASSWORD` | `your_password` | 可选 - 访问密码保护 |
   
   **获取 Brave API Key：** https://brave.com/search/api/

4. **部署**
   - 点击 **Create Web Service**
   - 等待部署完成（约2-3分钟）
   - 访问 `https://social-style-radar.onrender.com`

---

### 方法2：手动部署（无需 GitHub）

1. **安装 Render CLI**
   ```bash
   npm install -g @render/cli
   ```

2. **登录**
   ```bash
   render login
   ```

3. **部署**
   ```bash
   cd ~/.openclaw/workspace-daily-style/agents/daily_style/social-style-radar
   render deploy
   ```

4. **配置环境变量**
   ```bash
   render env set BRAVE_API_KEY your_brave_api_key
   render env set APP_PASSWORD your_password
   ```

---

## 🔐 安全配置

### 启用密码保护

在 Render 环境变量中设置：
```
APP_PASSWORD=your_strong_password
```

**不设置 `APP_PASSWORD`** = 公开访问（任何人都可以用）

**设置 `APP_PASSWORD`** = 需要登录才能使用

---

## 🧪 本地测试部署配置

```bash
# 1. 设置环境变量
export BRAVE_API_KEY="your_brave_api_key"
export APP_PASSWORD="test123"
export PORT=8898

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动（模拟 Render 环境）
gunicorn "web:create_app()" --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

访问：http://localhost:8898

---

## 📊 部署后验证

### 健康检查
```bash
curl https://social-style-radar.onrender.com/healthz
# 预期输出：{"ok": true}
```

### 功能测试
1. 访问首页：应该看到分类按钮和搜索框
2. 如果设置了密码：应该跳转到登录页
3. 搜索测试：输入"证件照"，点击搜索，应该返回结果

---

## 🐛 故障排查

### 部署失败

**检查日志：**
- Render Dashboard → Logs 标签
- 查找错误信息

**常见问题：**

1. **`ModuleNotFoundError: No module named 'Flask'`**
   - 检查 `requirements.txt` 是否正确
   - 确保 `buildCommand` 执行了 `pip install -r requirements.txt`

2. **`Application failed to start`**
   - 检查 `gunicorn` 启动命令是否正确
   - 确认 `PORT` 环境变量可用

3. **`BRAVE_API_KEY not found`**
   - 在 Render 环境变量中添加 `BRAVE_API_KEY`

### 搜索失败

**原因：**
- `BRAVE_API_KEY` 未配置或无效
- API 配额用尽

**解决：**
1. 检查环境变量是否正确设置
2. 访问 https://brave.com/search/api/ 检查配额

---

## 🔄 更新部署

### GitHub 方式
```bash
git add .
git commit -m "Update features"
git push origin main
```
Render 会自动检测并重新部署。

### 手动方式
```bash
render deploy
```

---

## 💰 费用说明

**Render Free Plan：**
- ✅ 免费额度：750 小时/月
- ✅ 自动休眠（15分钟无请求）
- ✅ 唤醒时间：~30秒
- ⚠️ 限制：512MB RAM

**升级到付费计划（可选）：**
- $7/月 - Starter Plan
- 无自动休眠
- 更多资源

---

## 📝 环境变量完整列表

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `BRAVE_API_KEY` | ✅ | - | Brave Search API 密钥 |
| `APP_PASSWORD` | ❌ | - | 访问密码（留空=公开） |
| `SESSION_SECRET` | ❌ | auto | Session 加密密钥（自动生成） |
| `PORT` | ❌ | auto | 端口（Render 自动分配） |

---

## 🌐 自定义域名（可选）

1. 在 Render Dashboard → Settings → Custom Domain
2. 添加你的域名（例如：`radar.yourdomain.com`）
3. 在域名 DNS 设置中添加 CNAME 记录：
   ```
   radar.yourdomain.com → social-style-radar.onrender.com
   ```

---

**部署完成后记得更新 MEMORY.md！** 🎯
