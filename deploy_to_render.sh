#!/bin/bash
# Social Style Radar - Render 快速部署脚本

set -e

echo "🚀 Social Style Radar - Render 部署准备"
echo ""

# 检查是否在正确目录
if [ ! -f "web.py" ]; then
    echo "❌ 错误：请在 social-style-radar 目录下运行此脚本"
    exit 1
fi

# 检查 git
if ! command -v git &> /dev/null; then
    echo "❌ 错误：未安装 git"
    exit 1
fi

# 初始化 git 仓库（如果还没有）
if [ ! -d ".git" ]; then
    echo "📦 初始化 Git 仓库..."
    git init
    git add .
    git commit -m "Initial commit: Social Style Radar Web"
fi

echo ""
echo "✅ 准备完成！"
echo ""
echo "📋 下一步操作："
echo ""
echo "1. 在 GitHub 创建新仓库："
echo "   https://github.com/new"
echo "   仓库名建议：social-style-radar"
echo ""
echo "2. 推送代码到 GitHub："
echo "   git remote add origin https://github.com/YOUR_USERNAME/social-style-radar.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. 在 Render 部署："
echo "   - 访问 https://dashboard.render.com"
echo "   - 点击 New → Web Service"
echo "   - 连接你的 GitHub 仓库"
echo "   - Render 会自动检测 render.yaml"
echo ""
echo "4. 配置环境变量："
echo "   BRAVE_API_KEY=your_api_key"
echo "   APP_PASSWORD=your_password (可选)"
echo ""
echo "5. 点击 Create Web Service，等待部署完成！"
echo ""
echo "💡 提示：获取 Brave API Key → https://brave.com/search/api/"
echo "📖 完整文档：查看 DEPLOY.md"
echo ""
