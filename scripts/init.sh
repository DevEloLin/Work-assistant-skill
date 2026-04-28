#!/bin/bash
# Miren Work Assistant 初始化脚本
# 用法: ./init.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MIREN_WORK_DIR="$HOME/.miren-work"

echo "Miren Work Assistant 初始化"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 创建目录结构
echo "1. 创建目录结构..."
mkdir -p "$MIREN_WORK_DIR/data/todos"
mkdir -p "$MIREN_WORK_DIR/data/reports/morning"
mkdir -p "$MIREN_WORK_DIR/data/reports/daily"
mkdir -p "$MIREN_WORK_DIR/data/reports/weekly"
mkdir -p "$MIREN_WORK_DIR/data/cache"
mkdir -p "$MIREN_WORK_DIR/data/logs"
echo "   ✅ 目录结构已创建: $MIREN_WORK_DIR"

# 复制配置文件
if [ ! -f "$MIREN_WORK_DIR/config.yaml" ]; then
    echo "2. 复制配置文件..."
    cp "$PROJECT_DIR/templates/config.yaml" "$MIREN_WORK_DIR/config.yaml"
    echo "   ✅ 配置文件已创建: $MIREN_WORK_DIR/config.yaml"
    echo "   ⚠️  请编辑配置文件，填入你的信息"
else
    echo "2. 配置文件已存在，跳过..."
fi

# 初始化待办任务文件
if [ ! -f "$MIREN_WORK_DIR/data/todos/active.json" ]; then
    echo "3. 初始化待办任务..."
    echo "[]" > "$MIREN_WORK_DIR/data/todos/active.json"
    echo "[]" > "$MIREN_WORK_DIR/data/todos/archive.json"
    echo "   ✅ 待办任务文件已创建"
else
    echo "3. 待办任务文件已存在，跳过..."
fi

# 检查依赖
echo "4. 检查依赖..."

# Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "   ✅ Python: $PYTHON_VERSION"
else
    echo "   ❌ Python3 未安装"
fi

# PyYAML
if python3 -c "import yaml" 2>/dev/null; then
    echo "   ✅ PyYAML 已安装"
else
    echo "   ⚠️  PyYAML 未安装，运行: pip3 install pyyaml"
fi

# requests (用于 Telegram)
if python3 -c "import requests" 2>/dev/null; then
    echo "   ✅ requests 已安装"
else
    echo "   ⚠️  requests 未安装，运行: pip3 install requests"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "初始化完成！"
echo ""
echo "下一步操作:"
echo "1. 编辑配置文件:"
echo "   nano $MIREN_WORK_DIR/config.yaml"
echo ""
echo "2. 安装定时任务:"
echo "   $SCRIPT_DIR/cron_manager.sh install"
echo ""
echo "3. 手动测试晨报:"
echo "   $SCRIPT_DIR/cron_manager.sh run morning"
echo ""
echo "4. 查看帮助:"
echo "   $SCRIPT_DIR/cron_manager.sh"
