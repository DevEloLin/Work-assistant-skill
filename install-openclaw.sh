#!/bin/bash
# Miren Work Assistant - OpenClaw 安装脚本
# 将 skill 安装到 OpenClaw workspace

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCLAW_WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SKILL_NAME="miren-work-assistant"

echo "Miren Work Assistant - OpenClaw 安装"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查 OpenClaw workspace
if [ ! -d "$OPENCLAW_WORKSPACE" ]; then
    echo "创建 OpenClaw workspace: $OPENCLAW_WORKSPACE"
    mkdir -p "$OPENCLAW_WORKSPACE/skills"
fi

# 创建 skill 目录
SKILL_DIR="$OPENCLAW_WORKSPACE/skills/$SKILL_NAME"
echo "安装 skill 到: $SKILL_DIR"

# 删除旧版本
if [ -d "$SKILL_DIR" ]; then
    echo "移除旧版本..."
    rm -rf "$SKILL_DIR"
fi

# 创建 skill 目录结构
mkdir -p "$SKILL_DIR"

# 复制 SKILL.md
cp "$SCRIPT_DIR/skills/miren-work-assistant/SKILL.md" "$SKILL_DIR/"

# 复制脚本目录
cp -r "$SCRIPT_DIR/scripts" "$SKILL_DIR/"

# 复制模板
cp -r "$SCRIPT_DIR/templates" "$SKILL_DIR/"

# 设置脚本可执行权限
chmod +x "$SKILL_DIR/scripts/"*.sh

echo ""
echo "✅ Skill 安装完成"
echo ""
echo "目录结构:"
echo "  $SKILL_DIR/"
echo "  ├── SKILL.md"
echo "  ├── scripts/"
echo "  │   ├── cron_manager.sh    # 直接调用 Agent CLI"
echo "  │   └── init.sh"
echo "  └── templates/"
echo "      └── config.yaml"
echo ""

# 运行初始化
echo "运行初始化..."
"$SKILL_DIR/scripts/init.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "下一步:"
echo ""
echo "1. 编辑配置文件:"
echo "   nano ~/.miren-work/config.yaml"
echo ""
echo "2. 设置 Telegram Bot Token:"
echo "   export TELEGRAM_BOT_TOKEN=\"your_token\""
echo ""
echo "3. 安装定时任务:"
echo "   $SKILL_DIR/scripts/cron_manager.sh install"
echo ""
echo "4. 在 OpenClaw 中使用（纯自然语言，无需命令）:"
echo "   晨报 / 检查邮件 / 日报 / 周报"
echo "   记一下: 修复登录 bug    (添加任务)"
echo "   完成了 修复登录 bug     (标记完成)"
