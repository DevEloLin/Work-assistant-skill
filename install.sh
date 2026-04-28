#!/bin/bash
# Miren Work Assistant - 统一安装脚本
# 支持 Claude Code 和 OpenClaw

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Miren Work Assistant - 安装向导"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检测可用的平台
OPENCLAW_AVAILABLE=false
CLAUDE_CODE_AVAILABLE=false

if [ -d "$HOME/.openclaw" ] || command -v openclaw &> /dev/null; then
    OPENCLAW_AVAILABLE=true
fi

if [ -d "$HOME/.claude" ] || command -v claude &> /dev/null; then
    CLAUDE_CODE_AVAILABLE=true
fi

# 显示检测结果
echo "检测到的平台:"
if [ "$OPENCLAW_AVAILABLE" = true ]; then
    echo "  ✅ OpenClaw"
fi
if [ "$CLAUDE_CODE_AVAILABLE" = true ]; then
    echo "  ✅ Claude Code"
fi
if [ "$OPENCLAW_AVAILABLE" = false ] && [ "$CLAUDE_CODE_AVAILABLE" = false ]; then
    echo "  ⚠️  未检测到已安装的平台"
    echo ""
    echo "请选择要安装的平台:"
fi

echo ""

# 处理命令行参数
if [ "$1" = "--openclaw" ]; then
    exec "$SCRIPT_DIR/install-openclaw.sh"
elif [ "$1" = "--claude-code" ]; then
    exec "$SCRIPT_DIR/install-claude-code.sh"
elif [ "$1" = "--both" ]; then
    echo "安装到 OpenClaw..."
    "$SCRIPT_DIR/install-openclaw.sh"
    echo ""
    echo "安装到 Claude Code..."
    "$SCRIPT_DIR/install-claude-code.sh"
    exit 0
fi

# 交互式选择
echo "选择安装目标:"
echo "  1) OpenClaw"
echo "  2) Claude Code"
echo "  3) 两者都安装"
echo "  q) 退出"
echo ""
read -p "请选择 [1-3/q]: " choice

case $choice in
    1)
        exec "$SCRIPT_DIR/install-openclaw.sh"
        ;;
    2)
        exec "$SCRIPT_DIR/install-claude-code.sh"
        ;;
    3)
        echo ""
        echo "安装到 OpenClaw..."
        "$SCRIPT_DIR/install-openclaw.sh"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "安装到 Claude Code..."
        "$SCRIPT_DIR/install-claude-code.sh"
        ;;
    q|Q)
        echo "已取消"
        exit 0
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac
