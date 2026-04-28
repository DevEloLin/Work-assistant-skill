#!/bin/bash
# Miren Work Assistant - Cron 定时任务管理脚本
# 用法: ./cron_manager.sh [install|uninstall|status|start|stop]
#
# 定时任务按用户配置的时区执行：
# - 晨报: 本地 08:30
# - 邮件检查: 本地 09:00-18:00 每小时
# - 日报: 本地 18:00
# - 周报: 本地 10:30 (周五)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIREN_WORK_DIR="$HOME/.miren-work"
LOG_FILE="$MIREN_WORK_DIR/data/logs/cron.log"
CRON_TAG="# MIREN-WORK-ASSISTANT"

# 确保目录存在
mkdir -p "$MIREN_WORK_DIR/data/logs"

# Python 解释器路径
PYTHON=$(which python3)

# 本地时间定义（用户期望的执行时间）
LOCAL_MORNING_TIME="08:30"        # 晨报
LOCAL_EMAIL_START="09"            # 邮件检查开始小时
LOCAL_EMAIL_END="18"              # 邮件检查结束小时
LOCAL_DAILY_TIME="18:00"          # 日报
LOCAL_WEEKLY_TIME="10:30"         # 周报（周五）

# 从配置文件读取时区
get_timezone() {
    if [ -f "$MIREN_WORK_DIR/config.yaml" ]; then
        local tz=$(grep -E "^\s*timezone:" "$MIREN_WORK_DIR/config.yaml" | head -1 | sed 's/.*timezone:\s*"\?\([^"]*\)"\?.*/\1/' | tr -d '[:space:]')
        if [ -n "$tz" ]; then
            echo "$tz"
            return
        fi
    fi
    echo "Asia/Shanghai"
}

# 将本地时间转换为 UTC cron 表达式
# 参数: local_time (HH:MM), day_of_week (可选, 0-6 或 *)
local_to_utc_cron() {
    local local_time="$1"
    local dow="${2:-*}"
    local tz=$(get_timezone)

    if command -v python3 &> /dev/null; then
        python3 -c "
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

local_time = '$local_time'
dow = '$dow'
tz_name = '$tz'

try:
    tz = ZoneInfo(tz_name)
    utc = ZoneInfo('UTC')

    # Parse local time
    hour, minute = map(int, local_time.split(':'))

    # Create a datetime in local timezone (use a reference date)
    local_dt = datetime(2024, 1, 1, hour, minute, tzinfo=tz)

    # Convert to UTC
    utc_dt = local_dt.astimezone(utc)

    # Output cron format: minute hour * * dow
    print(f'{utc_dt.minute} {utc_dt.hour} * * {dow}')
except Exception as e:
    # Fallback: assume UTC+8
    hour, minute = map(int, local_time.split(':'))
    utc_hour = (hour - 8) % 24
    print(f'{minute} {utc_hour} * * {dow}')
" 2>/dev/null
    else
        # Fallback without python
        echo "30 1 * * $dow"
    fi
}

# 获取邮件检查的 UTC cron 表达式（小时范围）
get_email_check_cron() {
    local tz=$(get_timezone)

    if command -v python3 &> /dev/null; then
        python3 -c "
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

tz_name = '$tz'
local_start = $LOCAL_EMAIL_START
local_end = $LOCAL_EMAIL_END

try:
    tz = ZoneInfo(tz_name)
    utc = ZoneInfo('UTC')

    # Convert start hour
    local_start_dt = datetime(2024, 1, 1, local_start, 0, tzinfo=tz)
    utc_start_dt = local_start_dt.astimezone(utc)
    utc_start = utc_start_dt.hour

    # Convert end hour
    local_end_dt = datetime(2024, 1, 1, local_end, 0, tzinfo=tz)
    utc_end_dt = local_end_dt.astimezone(utc)
    utc_end = utc_end_dt.hour

    # Handle day boundary crossing
    if utc_start <= utc_end:
        print(f'0 {utc_start}-{utc_end} * * *')
    else:
        # Crosses midnight, need two ranges
        print(f'0 {utc_start}-23,0-{utc_end} * * *')
except Exception as e:
    # Fallback
    print('0 2-11 * * *')
" 2>/dev/null
    else
        echo "0 2-11 * * *"
    fi
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

get_cron_jobs() {
    crontab -l 2>/dev/null | grep "$CRON_TAG" || true
}

install_cron() {
    log "安装定时任务..."

    local tz=$(get_timezone)
    log "使用时区: $tz"

    # 计算 UTC cron 表达式
    local morning_cron=$(local_to_utc_cron "$LOCAL_MORNING_TIME" "*")
    local email_cron=$(get_email_check_cron)
    local daily_cron=$(local_to_utc_cron "$LOCAL_DAILY_TIME" "*")
    local weekly_cron=$(local_to_utc_cron "$LOCAL_WEEKLY_TIME" "5")

    log "晨报 cron: $morning_cron (本地 $LOCAL_MORNING_TIME)"
    log "邮件 cron: $email_cron (本地 ${LOCAL_EMAIL_START}:00-${LOCAL_EMAIL_END}:00)"
    log "日报 cron: $daily_cron (本地 $LOCAL_DAILY_TIME)"
    log "周报 cron: $weekly_cron (本地 $LOCAL_WEEKLY_TIME 周五)"

    # 备份现有 crontab
    crontab -l > /tmp/current_cron 2>/dev/null || true

    # 移除旧的 miren-work 任务
    grep -v "$CRON_TAG" /tmp/current_cron > /tmp/new_cron 2>/dev/null || true

    # 添加新任务
    cat >> /tmp/new_cron << EOF
$morning_cron $PYTHON $SCRIPT_DIR/morning_report.py >> $LOG_FILE 2>&1 $CRON_TAG
$email_cron $PYTHON $SCRIPT_DIR/email_check.py >> $LOG_FILE 2>&1 $CRON_TAG
$daily_cron $PYTHON $SCRIPT_DIR/daily_summary.py >> $LOG_FILE 2>&1 $CRON_TAG
$weekly_cron $PYTHON $SCRIPT_DIR/weekly_report.py >> $LOG_FILE 2>&1 $CRON_TAG
EOF

    # 安装新 crontab
    crontab /tmp/new_cron
    rm -f /tmp/current_cron /tmp/new_cron

    log "定时任务安装完成"
    echo ""
    echo "已安装的定时任务:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "时区: $tz"
    echo ""
    echo "1. 每日晨报:     本地 $LOCAL_MORNING_TIME"
    echo "2. 邮件检查:     本地 ${LOCAL_EMAIL_START}:00-${LOCAL_EMAIL_END}:00 每小时"
    echo "3. 每日工作总结: 本地 $LOCAL_DAILY_TIME"
    echo "4. 周报生成:     本地 $LOCAL_WEEKLY_TIME (周五)"
    echo ""
    echo "注意: Cron 任务已转换为 UTC 时间执行"
    echo ""
}

uninstall_cron() {
    log "卸载定时任务..."

    # 备份现有 crontab
    crontab -l > /tmp/current_cron 2>/dev/null || true

    # 移除 miren-work 任务
    grep -v "$CRON_TAG" /tmp/current_cron > /tmp/new_cron 2>/dev/null || true

    # 安装新 crontab
    crontab /tmp/new_cron
    rm -f /tmp/current_cron /tmp/new_cron

    log "定时任务已卸载"
}

show_status() {
    echo "Miren Work Assistant - 定时任务状态"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    local jobs=$(get_cron_jobs)
    local tz=$(get_timezone)

    if [ -z "$jobs" ]; then
        echo "状态: ❌ 未安装"
        echo ""
        echo "使用 './cron_manager.sh install' 安装定时任务"
    else
        echo "状态: ✅ 运行中"
        echo "时区: $tz"
        echo ""
        echo "已安装的任务 (Cron UTC 时间):"
        echo "$jobs" | while read line; do
            echo "  • $line"
        done
        echo ""
        echo "本地执行时间:"
        echo "  $LOCAL_MORNING_TIME - 每日晨报"
        echo "  ${LOCAL_EMAIL_START}:00-${LOCAL_EMAIL_END}:00 - 每小时邮件检查"
        echo "  $LOCAL_DAILY_TIME - 每日工作总结"
        echo "  $LOCAL_WEEKLY_TIME (周五) - 周报生成"
    fi

    echo ""
    echo "日志文件: $LOG_FILE"

    if [ -f "$LOG_FILE" ]; then
        echo ""
        echo "最近日志:"
        tail -5 "$LOG_FILE" 2>/dev/null | while read line; do
            echo "  $line"
        done
    fi
}

run_now() {
    local task=$1
    case $task in
        morning)
            log "手动执行晨报..."
            $PYTHON "$SCRIPT_DIR/morning_report.py"
            ;;
        email)
            log "手动执行邮件检查..."
            $PYTHON "$SCRIPT_DIR/email_check.py"
            ;;
        summary)
            log "手动执行工作总结..."
            $PYTHON "$SCRIPT_DIR/daily_summary.py"
            ;;
        weekly)
            log "手动执行周报..."
            $PYTHON "$SCRIPT_DIR/weekly_report.py"
            ;;
        *)
            echo "未知任务: $task"
            echo "可用任务: morning, email, summary, weekly"
            exit 1
            ;;
    esac
}

case "$1" in
    install)
        install_cron
        ;;
    uninstall)
        uninstall_cron
        ;;
    status)
        show_status
        ;;
    run)
        run_now "$2"
        ;;
    *)
        echo "Miren Work Assistant - Cron 管理工具"
        echo ""
        echo "用法: $0 [命令]"
        echo ""
        echo "命令:"
        echo "  install     安装定时任务"
        echo "  uninstall   卸载定时任务"
        echo "  status      查看任务状态"
        echo "  run <task>  立即执行任务"
        echo ""
        echo "可执行任务:"
        echo "  morning   每日晨报"
        echo "  email     邮件检查"
        echo "  summary   每日工作总结"
        echo "  weekly    周报生成"
        echo ""
        echo "示例:"
        echo "  $0 install          # 安装定时任务"
        echo "  $0 status           # 查看状态"
        echo "  $0 run morning      # 手动执行晨报"
        echo "  $0 run weekly       # 手动执行周报"
        ;;
esac
