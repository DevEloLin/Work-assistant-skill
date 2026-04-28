#!/bin/bash
# Miren Work Assistant - Claude Code 安装脚本
# 将 skill 安装到 Claude Code skills 目录

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
SKILL_NAME="miren-work-assistant"

echo "Miren Work Assistant - Claude Code 安装"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 创建 Claude Code skills 目录
if [ ! -d "$CLAUDE_SKILLS_DIR" ]; then
    echo "创建 Claude Code skills 目录: $CLAUDE_SKILLS_DIR"
    mkdir -p "$CLAUDE_SKILLS_DIR"
fi

# 创建 skill 目录
SKILL_DIR="$CLAUDE_SKILLS_DIR/$SKILL_NAME"
echo "安装 skill 到: $SKILL_DIR"

# 删除旧版本
if [ -d "$SKILL_DIR" ]; then
    echo "移除旧版本..."
    rm -rf "$SKILL_DIR"
fi

# 创建 skill 目录结构
mkdir -p "$SKILL_DIR"

# 复制 SKILL.md (Claude Code 也支持此格式)
cp "$SCRIPT_DIR/skills/miren-work-assistant/SKILL.md" "$SKILL_DIR/"

# 复制脚本目录
cp -r "$SCRIPT_DIR/scripts" "$SKILL_DIR/"

# 复制模板
cp -r "$SCRIPT_DIR/templates" "$SKILL_DIR/"

# 设置脚本可执行权限
chmod +x "$SKILL_DIR/scripts/"*.sh
chmod +x "$SKILL_DIR/scripts/"*.py

echo ""
echo "✅ Skill 安装完成"
echo ""

# 运行初始化
echo "运行初始化..."
"$SKILL_DIR/scripts/init.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "在 Claude Code 中使用:"
echo "  /work report morning"
echo "  /work todo list"
