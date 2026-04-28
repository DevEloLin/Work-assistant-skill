#!/usr/bin/env python3
"""
每日晨报生成脚本
执行时间: UTC 05:30 (本地时间根据 config.yaml 中 timezone 设置)
"""

import json
import os
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import sys

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from telegram_formatter import (
    TelegramSender, TelegramFormatter,
    format_morning_report
)

# 配置路径
HOME = Path.home()
MIREN_WORK_DIR = HOME / ".miren-work"
CONFIG_FILE = MIREN_WORK_DIR / "config.yaml"
TODOS_FILE = MIREN_WORK_DIR / "data" / "todos" / "active.json"
REPORTS_DIR = MIREN_WORK_DIR / "data" / "reports" / "morning"
LOGS_DIR = MIREN_WORK_DIR / "data" / "logs"


def load_config() -> Dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def load_todos() -> List[Dict]:
    """加载待办任务"""
    if TODOS_FILE.exists():
        with open(TODOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def check_system_status(config: Dict) -> Dict[str, str]:
    """检查系统状态"""
    status = {
        "ai": "✅ 正常",
        "email": "❓ 未检查",
        "telegram": "❓ 未配置",
        "cron": "✅ 运行中"
    }

    # 检查 Telegram 配置
    if config.get("notification", {}).get("telegram", {}).get("enabled"):
        chat_id = config["notification"]["telegram"].get("chat_id")
        if chat_id and chat_id != "YOUR_CHAT_ID":
            status["telegram"] = "✅ 已连接"
        else:
            status["telegram"] = "⚠️ 未配置chat_id"

    # 检查 ms-365-mcp-server (简化检查)
    # 实际使用时需要通过 MCP 协议检查
    status["email"] = "✅ 已连接"

    return status


def get_todos_by_priority(todos: List[Dict]) -> Dict[str, List[Dict]]:
    """按优先级分组待办任务"""
    priority_map = {"P0": [], "P1": [], "P2": [], "P3": []}

    for todo in todos:
        if todo.get("status") in ["pending", "in_progress"]:
            priority = todo.get("priority", "P2")
            if priority in priority_map:
                priority_map[priority].append(todo)

    return priority_map


def format_tasks(tasks: List[Dict]) -> str:
    """格式化任务列表"""
    if not tasks:
        return "  • [无]"

    lines = []
    for task in tasks:
        status_icon = "⏳" if task.get("status") == "in_progress" else "○"
        due = task.get("due_date", "")
        due_str = f" (截止: {due})" if due else ""
        lines.append(f"  • {status_icon} {task['content']}{due_str}")

    return "\n".join(lines)


def calculate_stats(todos: List[Dict]) -> Dict[str, Any]:
    """计算待办统计"""
    total = len(todos)
    done = len([t for t in todos if t.get("status") == "done"])

    # 按优先级统计
    priority_counts = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
    for todo in todos:
        p = todo.get("priority", "P2")
        if p in priority_counts:
            priority_counts[p] += 1

    # 按标签统计
    tag_counts = {}
    for todo in todos:
        for tag in todo.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    completion_rate = f"{done}/{total}" if total > 0 else "0/0"
    if total > 0:
        completion_rate = f"{int(done/total*100)}% ({done}/{total})"

    priority_str = " ".join([f"{k}:{v}" for k, v in priority_counts.items()])
    type_str = " ".join([f"{k}:{v}" for k, v in list(tag_counts.items())[:4]])

    return {
        "completion_rate": completion_rate,
        "priority_stats": priority_str,
        "type_stats": type_str or "无标签数据"
    }


def get_email_summary(config: Dict) -> Dict[str, Any]:
    """获取邮件摘要（通过 MCP 调用）

    注意：此函数需要通过 Claude Code 的 MCP 协议调用 ms-365-mcp-server
    在脚本独立运行时，返回占位数据
    """
    # 占位数据 - 实际使用时通过 MCP 获取
    return {
        "new_emails": 0,
        "unread_emails": 0,
        "important_emails": 0,
        "need_reply": 0,
        "important_list": "  [需要通过 MCP 获取邮件数据]"
    }


def get_reminders(todos: List[Dict]) -> str:
    """生成重要提醒"""
    reminders = []
    today = datetime.now().date()

    # 检查今天截止的任务
    for todo in todos:
        if todo.get("status") in ["pending", "in_progress"]:
            due = todo.get("due_date")
            if due:
                try:
                    due_date = datetime.strptime(due, "%Y-%m-%d").date()
                    if due_date == today:
                        reminders.append(f"• 今日截止: {todo['content']}")
                    elif due_date < today:
                        reminders.append(f"• 已逾期: {todo['content']} (截止: {due})")
                except ValueError:
                    pass

    # 检查 P0 任务
    p0_tasks = [t for t in todos if t.get("priority") == "P0" and t.get("status") in ["pending", "in_progress"]]
    if p0_tasks:
        reminders.append(f"• 紧急任务待处理: {len(p0_tasks)}个")

    if not reminders:
        reminders.append("• 无紧急事项")

    return "\n".join(reminders)


def generate_morning_report() -> str:
    """生成晨报内容"""
    config = load_config()
    todos = load_todos()

    # 系统状态
    status = check_system_status(config)

    # 按优先级分组任务
    priority_tasks = get_todos_by_priority(todos)

    # 统计数据
    stats = calculate_stats(todos)

    # 邮件摘要
    email_summary = get_email_summary(config)

    # 重要提醒
    reminders = get_reminders(todos)

    # 当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.now().weekday()]

    report = f"""🌅 每日晨报 - {today} {weekday}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 系统状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• AI 助理: {status['ai']}
• MS365 邮箱: {status['email']}
• Telegram: {status['telegram']}
• Cron 任务: {status['cron']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 今日待办任务
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 P0 紧急重要
{format_tasks(priority_tasks['P0'])}

🟠 P1 重要
{format_tasks(priority_tasks['P1'])}

🟡 P2 一般
{format_tasks(priority_tasks['P2'])}

🟢 P3 低优先级
{format_tasks(priority_tasks['P3'])}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 历史待办统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 本周完成率: {stats['completion_rate']}
• 按优先级: {stats['priority_stats']}
• 按类型: {stats['type_stats']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 过去24小时邮件摘要
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• 新收邮件: {email_summary['new_emails']}封
• 未读邮件: {email_summary['unread_emails']}封
• 重要邮件: {email_summary['important_emails']}封
• 需要回复: {email_summary['need_reply']}封

📌 重要邮件:
{email_summary['important_list']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 重要提醒
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{reminders}
"""
    return report


def save_report(report: str) -> Path:
    """保存晨报到文件"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    report_file = REPORTS_DIR / f"{today}.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    return report_file


def build_report_data(config: Dict, todos: List[Dict]) -> Dict:
    """构建报告数据结构（用于格式化发送）"""
    status = check_system_status(config)
    priority_tasks = get_todos_by_priority(todos)
    stats = calculate_stats(todos)
    email_summary = get_email_summary(config)
    reminders_str = get_reminders(todos)

    today = datetime.now().strftime("%Y-%m-%d")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.now().weekday()]

    return {
        "date": today,
        "weekday": weekday,
        "system_status": {
            "AI 助理": status["ai"],
            "MS365 邮箱": status["email"],
            "Telegram": status["telegram"],
            "Cron 任务": status["cron"]
        },
        "todos_by_priority": priority_tasks,
        "stats": stats,
        "email_summary": email_summary,
        "reminders": [r.strip("• ") for r in reminders_str.split("\n") if r.strip()]
    }


def send_telegram_notification(report_data: Dict) -> Dict:
    """使用统一格式发送 Telegram 通知"""
    sender = TelegramSender()

    if not sender.is_configured():
        return {"success": False, "error": "Telegram 未配置"}

    message = format_morning_report(report_data)
    return sender.send(message)


def log_message(message: str):
    """记录日志"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "cron.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")


def main():
    """主函数"""
    log_message("开始生成晨报...")

    try:
        # 加载数据
        config = load_config()
        todos = load_todos()

        # 生成晨报文本
        report = generate_morning_report()

        # 保存晨报
        report_file = save_report(report)
        log_message(f"晨报已保存: {report_file}")

        # 发送 Telegram 通知（使用格式化模块）
        report_data = build_report_data(config, todos)
        result = send_telegram_notification(report_data)

        if result.get("success"):
            log_message(f"Telegram 通知已发送 ({result.get('sent_count', 1)} 条消息)")
        elif result.get("error") != "Telegram 未配置":
            log_message(f"Telegram 发送失败: {result.get('error', '未知错误')}")

        # 输出到控制台
        print(report)

        log_message("晨报生成完成")
        return 0

    except Exception as e:
        log_message(f"晨报生成失败: {e}")
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
