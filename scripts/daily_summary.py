#!/usr/bin/env python3
"""
每日工作总结脚本
执行时间: UTC 14:00 (本地时间根据 config.yaml 中 timezone 设置)
数据来源: 发送邮件 + 已完成任务
"""

import json
import os
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter
import sys

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from telegram_formatter import (
    TelegramSender, TelegramFormatter,
    format_daily_summary
)

# 配置路径
HOME = Path.home()
MIREN_WORK_DIR = HOME / ".miren-work"
CONFIG_FILE = MIREN_WORK_DIR / "config.yaml"
TODOS_FILE = MIREN_WORK_DIR / "data" / "todos" / "active.json"
REPORTS_DIR = MIREN_WORK_DIR / "data" / "reports" / "daily"
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


def classify_email_work(subject: str, body: str = "") -> str:
    """根据邮件内容分类工作类型"""
    subject_lower = subject.lower()
    body_lower = body.lower() if body else ""

    # 工单处理
    if any(kw in subject_lower for kw in ["jira", "工单", "ticket", "bug", "issue", "incident"]):
        return "工单处理"

    # 代码审查
    if any(kw in subject_lower for kw in ["review", "pr", "pull request", "代码", "merge", "审查"]):
        return "代码审查"

    # 报告撰写
    if any(kw in subject_lower for kw in ["report", "报告", "总结", "汇报", "文档"]):
        return "报告撰写"

    # 会议沟通
    if any(kw in subject_lower for kw in ["meeting", "会议", "讨论", "sync", "standup"]):
        return "会议沟通"

    # 部署运维
    if any(kw in subject_lower for kw in ["deploy", "部署", "release", "发布", "运维", "ops"]):
        return "部署运维"

    # 团队协作（发给多人或团队）
    # 这个需要根据收件人判断，简化处理
    if any(kw in subject_lower for kw in ["team", "all", "sync", "update", "通知"]):
        return "团队协作"

    return "日常沟通"


def get_sent_emails(config: Dict) -> List[Dict]:
    """获取今日发送的邮件

    注意：此函数需要通过 MCP 协议调用 ms-365-mcp-server
    在脚本独立运行时，返回占位数据
    """
    # 占位数据 - 实际使用时通过 MCP 获取
    # MCP 调用示例:
    # ms_graph_list_messages(folder="sentitems", top=50, filter="sentDateTime ge today")
    return []


def analyze_sent_emails(emails: List[Dict]) -> Dict[str, Any]:
    """分析发送的邮件"""
    if not emails:
        return {
            "total": 0,
            "by_type": {},
            "details": [],
            "recipients": {},
            "keywords": []
        }

    # 按类型分类
    type_counter = Counter()
    details = []
    recipient_counter = Counter()
    all_subjects = []

    for email in emails:
        subject = email.get("subject", "无主题")
        body = email.get("bodyPreview", "")
        work_type = classify_email_work(subject, body)

        type_counter[work_type] += 1

        details.append({
            "type": work_type,
            "subject": subject,
            "time": email.get("sentDateTime", ""),
            "to": email.get("toRecipients", [])
        })

        # 统计收件人
        for recipient in email.get("toRecipients", []):
            addr = recipient.get("emailAddress", {}).get("address", "")
            if addr:
                recipient_counter[addr] += 1

        all_subjects.append(subject)

    # 提取关键词（简化实现）
    keywords = extract_keywords(all_subjects)

    return {
        "total": len(emails),
        "by_type": dict(type_counter),
        "details": details,
        "recipients": dict(recipient_counter.most_common(5)),
        "keywords": keywords
    }


def extract_keywords(subjects: List[str]) -> List[str]:
    """从邮件主题提取关键词"""
    # 简化的关键词提取
    common_keywords = [
        "部署", "测试", "修复", "审查", "文档", "开发", "优化",
        "上线", "回滚", "配置", "监控", "告警", "需求", "设计",
        "deploy", "fix", "review", "test", "release", "update"
    ]

    found = []
    text = " ".join(subjects).lower()

    for kw in common_keywords:
        if kw.lower() in text:
            found.append(f"#{kw}")

    return found[:5]  # 最多返回5个


def get_completed_todos_today(todos: List[Dict]) -> List[Dict]:
    """获取今日完成的任务"""
    today = datetime.now().strftime("%Y-%m-%d")
    completed = []

    for todo in todos:
        if todo.get("status") == "done":
            updated = todo.get("updated_at", "")
            if updated.startswith(today):
                completed.append(todo)

    return completed


def get_tomorrow_plan(todos: List[Dict]) -> List[Dict]:
    """获取明日计划（未完成的高优先级任务）"""
    tomorrow_tasks = []

    for todo in todos:
        if todo.get("status") in ["pending", "in_progress"]:
            priority = todo.get("priority", "P2")
            if priority in ["P0", "P1", "P2"]:
                tomorrow_tasks.append(todo)

    # 按优先级排序
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    tomorrow_tasks.sort(key=lambda x: priority_order.get(x.get("priority", "P2"), 2))

    return tomorrow_tasks[:5]  # 最多返回5个


def generate_ai_summary(email_analysis: Dict, completed_todos: List[Dict]) -> str:
    """生成 AI 工作总结

    注意：实际使用时可调用 Claude API 生成更智能的总结
    """
    total_emails = email_analysis.get("total", 0)
    by_type = email_analysis.get("by_type", {})
    completed_count = len(completed_todos)

    if total_emails == 0 and completed_count == 0:
        return "今日暂无工作记录。"

    # 简单模板化总结
    summary_parts = []

    if total_emails > 0:
        main_work = max(by_type.items(), key=lambda x: x[1])[0] if by_type else "日常沟通"
        summary_parts.append(f"今日发送{total_emails}封邮件，主要工作集中在{main_work}方面")

    if completed_count > 0:
        summary_parts.append(f"完成{completed_count}项待办任务")

    if by_type.get("工单处理", 0) > 0:
        summary_parts.append(f"处理{by_type['工单处理']}个工单")

    if by_type.get("代码审查", 0) > 0:
        summary_parts.append(f"完成{by_type['代码审查']}次代码审查")

    return "，".join(summary_parts) + "。"


def format_email_work_details(details: List[Dict], limit: int = 10) -> str:
    """格式化邮件工作明细"""
    if not details:
        return "  • 暂无发送邮件记录"

    lines = []
    for item in details[:limit]:
        lines.append(f"  • [{item['type']}] {item['subject']}")

    if len(details) > limit:
        lines.append(f"  ... 还有 {len(details) - limit} 封")

    return "\n".join(lines)


def format_completed_todos(todos: List[Dict]) -> str:
    """格式化已完成任务"""
    if not todos:
        return "  • 暂无完成的任务"

    lines = []
    for todo in todos:
        priority = todo.get("priority", "P2")
        lines.append(f"  • {todo['content']} ({priority})")

    return "\n".join(lines)


def format_tomorrow_plan(todos: List[Dict]) -> str:
    """格式化明日计划"""
    if not todos:
        return "  • 暂无待办任务"

    lines = []
    for todo in todos:
        priority = todo.get("priority", "P2")
        status_icon = "⏳" if todo.get("status") == "in_progress" else "○"
        lines.append(f"  • {status_icon} {todo['content']} ({priority})")

    return "\n".join(lines)


def format_type_stats(by_type: Dict[str, int], total: int) -> str:
    """格式化类型统计"""
    if not by_type or total == 0:
        return "  暂无数据"

    lines = []
    for work_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
        percent = int(count / total * 100)
        bar = "█" * (percent // 10) + "░" * (10 - percent // 10)
        lines.append(f"  {work_type:<8} {bar}  {count}封 ({percent}%)")

    return "\n".join(lines)


def generate_daily_summary() -> str:
    """生成每日工作总结"""
    config = load_config()
    todos = load_todos()

    # 获取发送的邮件
    sent_emails = get_sent_emails(config)
    email_analysis = analyze_sent_emails(sent_emails)

    # 获取今日完成的任务
    completed_todos = get_completed_todos_today(todos)

    # 获取明日计划
    tomorrow_plan = get_tomorrow_plan(todos)

    # AI 总结
    ai_summary = generate_ai_summary(email_analysis, completed_todos)

    # 当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.now().weekday()]

    # 格式化各部分
    type_stats = format_type_stats(email_analysis["by_type"], email_analysis["total"])
    work_details = format_email_work_details(email_analysis["details"])
    completed_str = format_completed_todos(completed_todos)
    tomorrow_str = format_tomorrow_plan(tomorrow_plan)

    # 关键词
    keywords = " ".join(email_analysis.get("keywords", [])) or "暂无"

    report = f"""📊 每日工作总结 - {today} {weekday}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 邮件工作统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
发送邮件: {email_analysis['total']}封

{type_stats}

工作关键词: {keywords}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 工作明细
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{work_details}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 已完成任务 ({len(completed_todos)}项)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{completed_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 AI 总结
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{ai_summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 明日计划
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{tomorrow_str}
"""
    return report


def save_report(report: str) -> Path:
    """保存日报到文件"""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    report_file = REPORTS_DIR / f"{today}.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    return report_file


def build_summary_data(email_analysis: Dict, completed_todos: List[Dict],
                       tomorrow_plan: List[Dict], ai_summary: str) -> Dict:
    """构建总结数据结构（用于格式化发送）"""
    today = datetime.now().strftime("%Y-%m-%d")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][datetime.now().weekday()]

    return {
        "date": today,
        "weekday": weekday,
        "email_analysis": email_analysis,
        "work_details": email_analysis.get("details", []),
        "completed_todos": completed_todos,
        "tomorrow_plan": tomorrow_plan,
        "ai_summary": ai_summary
    }


def send_telegram_notification(summary_data: Dict) -> Dict:
    """使用统一格式发送 Telegram 通知"""
    sender = TelegramSender()

    if not sender.is_configured():
        return {"success": False, "error": "Telegram 未配置"}

    message = format_daily_summary(summary_data)
    return sender.send(message)


def log_message(message: str):
    """记录日志"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "cron.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] [SUMMARY] {message}\n")


def main():
    """主函数"""
    log_message("开始生成每日工作总结...")

    try:
        # 加载数据
        config = load_config()
        todos = load_todos()

        # 获取发送的邮件
        sent_emails = get_sent_emails(config)
        email_analysis = analyze_sent_emails(sent_emails)

        # 获取今日完成的任务
        completed_todos = get_completed_todos_today(todos)

        # 获取明日计划
        tomorrow_plan = get_tomorrow_plan(todos)

        # AI 总结
        ai_summary = generate_ai_summary(email_analysis, completed_todos)

        # 生成工作总结文本
        report = generate_daily_summary()

        # 保存报告
        report_file = save_report(report)
        log_message(f"工作总结已保存: {report_file}")

        # 发送 Telegram 通知（使用格式化模块）
        summary_data = build_summary_data(email_analysis, completed_todos, tomorrow_plan, ai_summary)
        result = send_telegram_notification(summary_data)

        if result.get("success"):
            log_message(f"Telegram 通知已发送 ({result.get('sent_count', 1)} 条消息)")
        elif result.get("error") != "Telegram 未配置":
            log_message(f"Telegram 发送失败: {result.get('error', '未知错误')}")

        # 输出到控制台
        print(report)

        log_message("每日工作总结生成完成")
        return 0

    except Exception as e:
        log_message(f"工作总结生成失败: {e}")
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
