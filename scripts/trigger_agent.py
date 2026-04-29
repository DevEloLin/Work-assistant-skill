#!/usr/bin/env python3
"""
触发 OpenClaw Agent 执行任务
通过 Telegram 发送触发消息，让 Agent 加载 skill 并生成报告
"""

import os
import sys
import yaml
import requests
from pathlib import Path
from datetime import datetime

# 配置路径
HOME = Path.home()
MIREN_WORK_DIR = HOME / ".miren-work"
CONFIG_FILE = MIREN_WORK_DIR / "config.yaml"
LOGS_DIR = MIREN_WORK_DIR / "data" / "logs"


def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}


def log_message(message: str):
    """记录日志"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "cron.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] [TRIGGER] {message}\n")


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> dict:
    """发送 Telegram 消息触发 Agent"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        response = requests.post(url, json=data, timeout=30)
        result = response.json()

        if result.get("ok"):
            return {"success": True}
        else:
            return {"success": False, "error": result.get("description", "Unknown error")}

    except Exception as e:
        return {"success": False, "error": str(e)}


def trigger_agent(task_type: str):
    """触发 Agent 执行指定任务"""
    config = load_config()

    # 获取 Telegram 配置
    tg_config = config.get("notification", {}).get("telegram", {})
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN") or tg_config.get("bot_token", "")
    chat_id = tg_config.get("chat_id", "")

    if not bot_token or not chat_id or chat_id == "YOUR_CHAT_ID":
        log_message(f"Telegram 未配置，无法触发 Agent")
        print("Error: Telegram not configured", file=sys.stderr)
        return 1

    # 触发消息映射
    trigger_messages = {
        "morning": "🌅 请生成今日晨报",
        "email": "📧 请检查邮件",
        "daily": "📊 请生成今日工作总结",
        "weekly": "📈 请生成本周周报"
    }

    message = trigger_messages.get(task_type)
    if not message:
        log_message(f"未知任务类型: {task_type}")
        print(f"Error: Unknown task type: {task_type}", file=sys.stderr)
        return 1

    # 添加时间戳
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_message = f"{message}\n<i>⏰ 定时任务触发 ({now})</i>"

    log_message(f"触发 Agent 执行: {task_type}")

    result = send_telegram_message(bot_token, chat_id, full_message)

    if result.get("success"):
        log_message(f"触发消息已发送: {task_type}")
        print(f"Triggered: {task_type}")
        return 0
    else:
        log_message(f"触发失败: {result.get('error')}")
        print(f"Error: {result.get('error')}", file=sys.stderr)
        return 1


def main():
    if len(sys.argv) < 2:
        print("Usage: trigger_agent.py <task_type>")
        print("Task types: morning, email, daily, weekly")
        return 1

    task_type = sys.argv[1]
    return trigger_agent(task_type)


if __name__ == "__main__":
    sys.exit(main())
