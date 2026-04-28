#!/usr/bin/env python3
"""
邮件检查脚本
执行时间: UTC 06:00-15:00 每小时 (本地时间根据 config.yaml 中 timezone 设置)
静默时间: UTC 16:00 - 次日 05:30
"""

import json
import os
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from telegram_formatter import (
    TelegramSender, TelegramFormatter,
    format_email_alert
)

# 配置路径
HOME = Path.home()
MIREN_WORK_DIR = HOME / ".miren-work"
CONFIG_FILE = MIREN_WORK_DIR / "config.yaml"
CACHE_DIR = MIREN_WORK_DIR / "data" / "cache"
LOGS_DIR = MIREN_WORK_DIR / "data" / "logs"


def load_config() -> Dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}


def is_silent_time(config: Dict) -> bool:
    """检查是否在静默时间内"""
    now = datetime.utcnow()
    silent_start = config.get("cron", {}).get("silent_start", "16:00")
    silent_end = config.get("cron", {}).get("silent_end", "05:30")

    try:
        start_hour, start_min = map(int, silent_start.split(":"))
        end_hour, end_min = map(int, silent_end.split(":"))

        current_minutes = now.hour * 60 + now.minute
        start_minutes = start_hour * 60 + start_min
        end_minutes = end_hour * 60 + end_min

        # 跨午夜的情况
        if start_minutes > end_minutes:
            return current_minutes >= start_minutes or current_minutes < end_minutes
        else:
            return start_minutes <= current_minutes < end_minutes

    except (ValueError, AttributeError):
        return False


def is_important_email(email: Dict, config: Dict) -> tuple[bool, str]:
    """判断邮件是否重要，返回 (是否重要, 原因)"""
    subject = email.get("subject", "").lower()
    body = email.get("body", "").lower()
    sender = email.get("from", "").lower()
    to_list = email.get("to", [])

    important_senders = config.get("email", {}).get("important_senders", [])
    important_keywords = config.get("email", {}).get("important_keywords", [])
    user_email = config.get("user", {}).get("email", "").lower()

    # 1. 工单更新
    ticket_keywords = ["jira", "工单", "ticket", "issue", "bug", "incident"]
    for kw in ticket_keywords:
        if kw in subject:
            return True, "工单更新"

    # 2. 被@提及
    user_name = config.get("user", {}).get("name", "")
    if user_name and f"@{user_name.lower()}" in body:
        return True, "被@提及"

    # 3. 安全告警
    alert_keywords = ["alert", "告警", "安全", "security", "warning", "critical", "urgent", "紧急"]
    for kw in alert_keywords:
        if kw in subject:
            return True, "安全告警"

    # 4. 配置的重要关键词
    for kw in important_keywords:
        if kw.lower() in subject or kw.lower() in body:
            return True, f"关键词: {kw}"

    # 5. 重要发件人
    for imp_sender in important_senders:
        if imp_sender.lower() in sender:
            return True, "重要发件人"

    # 6. 直接发送给用户（非CC）
    if user_email:
        for recipient in to_list:
            if isinstance(recipient, str) and user_email in recipient.lower():
                return True, "直接发送"

    return False, ""


def should_ignore_email(email: Dict) -> tuple[bool, str]:
    """判断是否应该忽略此邮件"""
    sender = email.get("from", "").lower()
    subject = email.get("subject", "").lower()
    body = email.get("body", "").lower()

    # 自动通知
    auto_senders = ["noreply", "no-reply", "automated", "notifications", "mailer-daemon"]
    for auto in auto_senders:
        if auto in sender:
            return True, "自动通知"

    # 订阅邮件
    if "unsubscribe" in body:
        return True, "订阅邮件"

    # 日历自动回复
    calendar_keywords = ["accepted", "declined", "tentative", "calendar"]
    for kw in calendar_keywords:
        if kw in subject and ("invitation" in subject or "meeting" in subject):
            return True, "日历回复"

    return False, ""


def get_sent_emails_summary(config: Dict) -> List[Dict]:
    """获取用户发送的邮件（用于工作总结）

    注意：此函数需要通过 MCP 协议调用 ms-365-mcp-server
    返回用户在过去24小时内发送的邮件列表
    """
    # 占位数据 - 实际使用时通过 MCP 获取
    return []


def summarize_work_from_sent_emails(sent_emails: List[Dict]) -> str:
    """根据发送的邮件总结当日工作"""
    if not sent_emails:
        return "今日暂无发送邮件记录"

    work_items = []

    for email in sent_emails:
        subject = email.get("subject", "")
        recipients = email.get("to", [])
        sent_time = email.get("sentDateTime", "")

        # 简单分类工作内容
        work_type = "沟通"
        if any(kw in subject.lower() for kw in ["jira", "工单", "ticket", "bug"]):
            work_type = "工单处理"
        elif any(kw in subject.lower() for kw in ["review", "审核", "pr", "代码"]):
            work_type = "代码审查"
        elif any(kw in subject.lower() for kw in ["report", "报告", "总结"]):
            work_type = "报告撰写"
        elif any(kw in subject.lower() for kw in ["meeting", "会议", "讨论"]):
            work_type = "会议沟通"

        work_items.append({
            "type": work_type,
            "subject": subject,
            "recipients": recipients,
            "time": sent_time
        })

    # 生成摘要
    summary_lines = []
    type_counts = {}

    for item in work_items:
        work_type = item["type"]
        type_counts[work_type] = type_counts.get(work_type, 0) + 1
        summary_lines.append(f"  • [{item['type']}] {item['subject']}")

    stats = " | ".join([f"{k}: {v}封" for k, v in type_counts.items()])

    return f"发送邮件统计: {stats}\n\n工作明细:\n" + "\n".join(summary_lines[:10])


def check_emails(config: Dict) -> Dict[str, Any]:
    """检查邮件（通过 MCP 调用）

    注意：此函数需要通过 Claude Code 的 MCP 协议调用 ms-365-mcp-server
    在脚本独立运行时，返回占位数据
    """
    # 占位实现 - 实际使用时通过 MCP 获取
    result = {
        "checked": True,
        "total": 0,
        "important": [],
        "ignored": 0,
        "sent_emails": [],  # 用户发送的邮件
        "work_summary": ""  # 基于发送邮件的工作总结
    }

    # 获取发送的邮件并生成工作总结
    sent_emails = get_sent_emails_summary(config)
    result["sent_emails"] = sent_emails
    result["work_summary"] = summarize_work_from_sent_emails(sent_emails)

    return result


def format_important_emails(emails: List[Dict]) -> str:
    """格式化重要邮件列表"""
    if not emails:
        return "无重要邮件"

    lines = []
    for i, email in enumerate(emails, 1):
        subject = email.get("subject", "无主题")
        sender = email.get("from", "未知发件人")
        reason = email.get("importance_reason", "")
        time = email.get("receivedDateTime", "")

        lines.append(f"{i}. [{reason}] {subject}")
        lines.append(f"   发件人: {sender}")
        if time:
            lines.append(f"   时间: {time}")
        lines.append("")

    return "\n".join(lines)


def send_telegram_notification(important_emails: List[Dict]) -> Dict:
    """使用统一格式发送 Telegram 通知"""
    sender = TelegramSender()

    if not sender.is_configured():
        return {"success": False, "error": "Telegram 未配置"}

    # 构建告警数据
    alert_data = {
        "important_emails": [
            {
                "reason": email.get("importance_reason", ""),
                "subject": email.get("subject", "无主题"),
                "from": email.get("from", ""),
                "time": email.get("receivedDateTime", "")
            }
            for email in important_emails
        ]
    }

    message = format_email_alert(alert_data)
    return sender.send(message)


def log_message(message: str):
    """记录日志"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "cron.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] [EMAIL] {message}\n")


def save_email_cache(result: Dict):
    """保存邮件缓存"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "email_cache.json"

    cache = {
        "last_check": datetime.now().isoformat(),
        "result": result
    }

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    config = load_config()

    # 检查是否在静默时间
    if is_silent_time(config):
        log_message("当前为静默时间，跳过邮件检查")
        print("当前为静默时间，跳过邮件检查")
        return 0

    log_message("开始检查邮件...")

    try:
        # 检查邮件
        result = check_emails(config)

        # 保存缓存
        save_email_cache(result)

        # 如果有重要邮件，发送通知
        if result["important"]:
            # 使用统一格式化模块发送
            send_result = send_telegram_notification(result["important"])

            if send_result.get("success"):
                log_message(f"发现 {len(result['important'])} 封重要邮件，已推送通知 ({send_result.get('sent_count', 1)} 条)")
            elif send_result.get("error") != "Telegram 未配置":
                log_message(f"Telegram 发送失败: {send_result.get('error', '未知错误')}")

            # 控制台输出
            print(format_important_emails(result["important"]))
        else:
            log_message("无重要邮件")
            print("邮件检查完成，无重要邮件")

        log_message("邮件检查完成")
        return 0

    except Exception as e:
        log_message(f"邮件检查失败: {e}")
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
