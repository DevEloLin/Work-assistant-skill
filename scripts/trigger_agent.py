#!/usr/bin/env python3
"""
触发 OpenClaw Agent 执行任务
通过 Telegram 发送触发消息，让 Agent 加载 skill 并生成报告
"""

import os
import sys
import json
import yaml
import requests
from pathlib import Path
from datetime import datetime

# 配置路径
HOME = Path.home()
OPENCLAW_CONFIG = HOME / ".openclaw" / "openclaw.json"
MIREN_WORK_DIR = HOME / ".miren-work"
MIREN_CONFIG_FILE = MIREN_WORK_DIR / "config.yaml"
LOGS_DIR = MIREN_WORK_DIR / "data" / "logs"


def load_telegram_config():
    """
    加载 Telegram 配置
    优先级：
    1. ~/.openclaw/openclaw.json
    2. ~/.miren-work/config.yaml
    3. 环境变量 TELEGRAM_BOT_TOKEN
    """
    bot_token = None
    chat_id = None

    # 1. 优先从 OpenClaw 配置读取
    if OPENCLAW_CONFIG.exists():
        try:
            with open(OPENCLAW_CONFIG, 'r', encoding='utf-8') as f:
                openclaw = json.load(f)
                # 尝试多种可能的配置路径
                if 'telegram' in openclaw:
                    bot_token = openclaw['telegram'].get('bot_token') or openclaw['telegram'].get('token')
                    chat_id = openclaw['telegram'].get('chat_id') or openclaw['telegram'].get('chatId')
                elif 'bot_token' in openclaw:
                    bot_token = openclaw.get('bot_token')
                    chat_id = openclaw.get('chat_id')
                # 也检查 notification 字段
                elif 'notification' in openclaw:
                    tg = openclaw['notification'].get('telegram', {})
                    bot_token = tg.get('bot_token') or tg.get('token')
                    chat_id = tg.get('chat_id') or tg.get('chatId')
        except Exception as e:
            pass

    # 2. 如果 OpenClaw 没有，从 miren-work 配置读取
    if (not bot_token or not chat_id) and MIREN_CONFIG_FILE.exists():
        try:
            with open(MIREN_CONFIG_FILE, 'r', encoding='utf-8') as f:
                miren = yaml.safe_load(f) or {}
                tg = miren.get('notification', {}).get('telegram', {})
                if not bot_token:
                    bot_token = tg.get('bot_token')
                if not chat_id:
                    chat_id = tg.get('chat_id')
        except Exception as e:
            pass

    # 3. 环境变量作为最后的备选
    if not bot_token:
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')

    return bot_token, chat_id


def load_config():
    """加载 miren-work 配置文件"""
    if MIREN_CONFIG_FILE.exists():
        with open(MIREN_CONFIG_FILE, 'r', encoding='utf-8') as f:
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
    # 获取 Telegram 配置（优先从 OpenClaw 读取）
    bot_token, chat_id = load_telegram_config()

    if not bot_token:
        log_message("Telegram bot_token 未配置")
        print("Error: Telegram bot_token not found", file=sys.stderr)
        print("Please configure in ~/.openclaw/openclaw.json or ~/.miren-work/config.yaml", file=sys.stderr)
        return 1

    if not chat_id or chat_id == "YOUR_CHAT_ID":
        log_message("Telegram chat_id 未配置")
        print("Error: Telegram chat_id not found", file=sys.stderr)
        print("Please configure in ~/.openclaw/openclaw.json or ~/.miren-work/config.yaml", file=sys.stderr)
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
