#!/usr/bin/env python3
"""
周报生成脚本
基于每日工作总结聚合生成本周报告
执行时间: 每周五 UTC 06:30 (本地时间根据 config.yaml 中 timezone 设置) 或手动触发
"""

import json
import os
import re
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
    format_weekly_report, send_weekly_report
)

# 配置路径
HOME = Path.home()
MIREN_WORK_DIR = HOME / ".miren-work"
CONFIG_FILE = MIREN_WORK_DIR / "config.yaml"
TODOS_FILE = MIREN_WORK_DIR / "data" / "todos" / "active.json"
DAILY_REPORTS_DIR = MIREN_WORK_DIR / "data" / "reports" / "daily"
WEEKLY_REPORTS_DIR = MIREN_WORK_DIR / "data" / "reports" / "weekly"
LOGS_DIR = MIREN_WORK_DIR / "data" / "logs"

# 中文星期
WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def load_config() -> Dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}


def load_todos() -> List[Dict]:
    """加载待办任务"""
    if TODOS_FILE.exists():
        with open(TODOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def get_week_range() -> tuple[datetime, datetime, str]:
    """获取本周的日期范围（周一到周日）"""
    today = datetime.now()
    # 获取本周一
    monday = today - timedelta(days=today.weekday())
    # 获取本周日
    sunday = monday + timedelta(days=6)

    range_str = f"{monday.strftime('%m/%d')} - {sunday.strftime('%m/%d')}"

    return monday, sunday, range_str


def get_week_dates(monday: datetime) -> List[datetime]:
    """获取一周的所有日期"""
    return [monday + timedelta(days=i) for i in range(7)]


def load_daily_report(date: datetime) -> Optional[Dict]:
    """加载指定日期的每日工作总结"""
    date_str = date.strftime("%Y-%m-%d")
    report_file = DAILY_REPORTS_DIR / f"{date_str}.md"

    if not report_file.exists():
        return None

    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 解析报告内容
        return parse_daily_report(content, date_str)
    except Exception as e:
        log_message(f"解析日报失败 {date_str}: {e}")
        return None


def parse_daily_report(content: str, date_str: str) -> Dict:
    """解析每日工作总结内容"""
    result = {
        "date": date_str,
        "emails_sent": 0,
        "work_by_type": {},
        "completed_tasks": [],
        "work_details": []
    }

    # 提取发送邮件数量
    email_match = re.search(r'发送邮件[：:]\s*(\d+)', content)
    if email_match:
        result["emails_sent"] = int(email_match.group(1))

    # 提取工作类型统计
    type_patterns = [
        r'工单处理[：:].+?(\d+)封',
        r'代码审查[：:].+?(\d+)封',
        r'会议沟通[：:].+?(\d+)封',
        r'日常沟通[：:].+?(\d+)封',
        r'报告撰写[：:].+?(\d+)封',
        r'部署运维[：:].+?(\d+)封',
        r'团队协作[：:].+?(\d+)封',
    ]

    type_names = ["工单处理", "代码审查", "会议沟通", "日常沟通", "报告撰写", "部署运维", "团队协作"]

    for pattern, name in zip(type_patterns, type_names):
        match = re.search(pattern, content)
        if match:
            result["work_by_type"][name] = int(match.group(1))

    # 提取已完成任务
    completed_section = re.search(r'已完成任务.*?\n(.*?)(?=\n━|$)', content, re.DOTALL)
    if completed_section:
        tasks = re.findall(r'[•○✅]\s*(.+?)(?:\s*\([P\d]\))?$', completed_section.group(1), re.MULTILINE)
        result["completed_tasks"] = [t.strip() for t in tasks if t.strip() and '暂无' not in t]

    # 提取工作明细
    details_section = re.search(r'工作明细.*?\n(.*?)(?=\n━|$)', content, re.DOTALL)
    if details_section:
        details = re.findall(r'\[(.+?)\]\s*(.+?)$', details_section.group(1), re.MULTILINE)
        result["work_details"] = [{"type": t, "subject": s.strip()} for t, s in details]

    return result


def aggregate_weekly_data(daily_reports: List[Dict]) -> Dict:
    """聚合本周数据"""
    # 总邮件数
    total_emails = sum(r.get("emails_sent", 0) for r in daily_reports)

    # 工作类型汇总
    work_distribution = Counter()
    for report in daily_reports:
        for work_type, count in report.get("work_by_type", {}).items():
            work_distribution[work_type] += count

    # 完成任务汇总
    all_completed = []
    for report in daily_reports:
        all_completed.extend(report.get("completed_tasks", []))

    # 每日统计
    daily_stats = []
    for report in daily_reports:
        date = datetime.strptime(report["date"], "%Y-%m-%d")
        daily_stats.append({
            "date": report["date"],
            "weekday": WEEKDAYS[date.weekday()],
            "emails": report.get("emails_sent", 0),
            "tasks": len(report.get("completed_tasks", []))
        })

    # 工作明细汇总（去重）
    all_details = []
    seen_subjects = set()
    for report in daily_reports:
        for detail in report.get("work_details", []):
            subject = detail.get("subject", "")
            if subject and subject not in seen_subjects:
                seen_subjects.add(subject)
                all_details.append(detail)

    return {
        "total_emails": total_emails,
        "work_distribution": dict(work_distribution),
        "completed_tasks": all_completed,
        "daily_stats": daily_stats,
        "work_details": all_details
    }


def get_completed_todos_this_week(todos: List[Dict], monday: datetime) -> List[Dict]:
    """获取本周完成的任务"""
    completed = []
    monday_str = monday.strftime("%Y-%m-%d")
    sunday = monday + timedelta(days=6)
    sunday_str = sunday.strftime("%Y-%m-%d")

    for todo in todos:
        if todo.get("status") == "done":
            updated = todo.get("updated_at", "")[:10]
            if monday_str <= updated <= sunday_str:
                completed.append(todo)

    return completed


def get_next_week_plan(todos: List[Dict]) -> List[Dict]:
    """获取下周计划（未完成的任务）"""
    pending_tasks = []

    for todo in todos:
        if todo.get("status") in ["pending", "in_progress"]:
            pending_tasks.append(todo)

    # 按优先级排序
    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    pending_tasks.sort(key=lambda x: priority_order.get(x.get("priority", "P2"), 2))

    return pending_tasks[:5]


def generate_highlights(aggregated: Dict, completed_todos: List[Dict]) -> List[str]:
    """生成本周重点完成事项"""
    highlights = []

    # 从完成的任务中提取高优先级的
    high_priority = [t for t in completed_todos if t.get("priority") in ["P0", "P1"]]
    for task in high_priority[:3]:
        highlights.append(task.get("content", ""))

    # 从工作明细中提取重要的
    important_types = ["工单处理", "代码审查", "部署运维"]
    for detail in aggregated.get("work_details", []):
        if detail.get("type") in important_types and len(highlights) < 6:
            highlights.append(detail.get("subject", ""))

    # 去重
    seen = set()
    unique_highlights = []
    for h in highlights:
        if h and h not in seen:
            seen.add(h)
            unique_highlights.append(h)

    return unique_highlights[:6]


def generate_ai_summary(aggregated: Dict, completed_todos: List[Dict]) -> str:
    """生成 AI 周总结"""
    total_emails = aggregated.get("total_emails", 0)
    work_dist = aggregated.get("work_distribution", {})
    completed_count = len(completed_todos)
    daily_count = len(aggregated.get("daily_stats", []))

    if total_emails == 0 and completed_count == 0:
        return "本周工作数据较少，建议保持工作记录习惯。"

    # 找出最主要的工作类型
    main_work = ""
    if work_dist:
        main_work = max(work_dist.items(), key=lambda x: x[1])[0]

    # 计算日均
    avg_emails = round(total_emails / max(daily_count, 1), 1)
    avg_tasks = round(completed_count / max(daily_count, 1), 1)

    summary_parts = []

    summary_parts.append(f"本周共工作{daily_count}天")
    summary_parts.append(f"发送{total_emails}封邮件（日均{avg_emails}封）")
    summary_parts.append(f"完成{completed_count}项任务（日均{avg_tasks}项）")

    if main_work:
        summary_parts.append(f"主要工作集中在{main_work}方面")

    # 工作分析
    if work_dist.get("工单处理", 0) > 5:
        summary_parts.append("工单处理量较大，注意跟进解决进度")

    if work_dist.get("会议沟通", 0) > total_emails * 0.3:
        summary_parts.append("会议沟通占比较高")

    return "。".join(summary_parts) + "。"


def generate_weekly_report() -> tuple[str, Dict]:
    """生成周报内容"""
    config = load_config()
    todos = load_todos()

    # 获取本周日期范围
    monday, sunday, week_range = get_week_range()
    week_dates = get_week_dates(monday)

    # 加载本周所有日报
    daily_reports = []
    for date in week_dates:
        report = load_daily_report(date)
        if report:
            daily_reports.append(report)

    # 聚合数据
    aggregated = aggregate_weekly_data(daily_reports)

    # 获取本周完成的任务
    completed_todos = get_completed_todos_this_week(todos, monday)

    # 获取下周计划
    next_week_plan = get_next_week_plan(todos)

    # 生成重点完成事项
    highlights = generate_highlights(aggregated, completed_todos)

    # 计算完成率
    total_tasks = len(completed_todos) + len([t for t in todos if t.get("status") in ["pending", "in_progress"]])
    completion_rate = f"{int(len(completed_todos) / max(total_tasks, 1) * 100)}%" if total_tasks > 0 else "N/A"

    # AI 总结
    ai_summary = generate_ai_summary(aggregated, completed_todos)

    # 构建报告数据
    report_data = {
        "week_range": week_range,
        "overview": {
            "total_emails": aggregated["total_emails"],
            "completed_tasks": len(completed_todos),
            "completion_rate": completion_rate,
            "working_days": len(daily_reports)
        },
        "work_distribution": aggregated["work_distribution"],
        "daily_stats": aggregated["daily_stats"],
        "highlights": highlights,
        "next_week_plan": next_week_plan,
        "ai_summary": ai_summary
    }

    # 生成文本报告
    f = TelegramFormatter

    lines = [
        f"📊 本周工作总结 - {week_range}",
        "",
        f.DIVIDER_THICK,
        f.section("工作概览", "📈")[1:],  # 去掉开头换行
    ]

    # 工作概览
    lines.append(f"  📧 发送邮件: {aggregated['total_emails']} 封")
    lines.append(f"  ✅ 完成任务: {len(completed_todos)} 项")
    lines.append(f"  📊 完成率: {completion_rate}")
    lines.append(f"  📆 工作天数: {len(daily_reports)} 天")

    # 工作分布
    lines.append(f.section("工作分布", "📋"))
    work_dist = aggregated["work_distribution"]
    if work_dist:
        total = sum(work_dist.values())
        for work_type, count in sorted(work_dist.items(), key=lambda x: -x[1]):
            icon = f.work_type_icon(work_type)
            bar = f.progress_bar(count, total, 8)
            lines.append(f"  {icon} {work_type}: {bar} ({count}封)")
    else:
        lines.append("  暂无数据")

    # 每日统计
    lines.append(f.section("每日工作量", "📆"))
    for day in aggregated["daily_stats"]:
        bar = f.progress_bar(day["emails"], 20, 6)
        lines.append(f"  {day['weekday']} ({day['date'][5:]}): {bar} 📧{day['emails']} ✅{day['tasks']}")

    # 如果没有数据的天
    if len(aggregated["daily_stats"]) < 5:
        lines.append(f"  (共 {7 - len(aggregated['daily_stats'])} 天无数据)")

    # 重点完成
    lines.append(f.section("本周重点完成", "🎯"))
    if highlights:
        for i, item in enumerate(highlights, 1):
            lines.append(f"  {i}. {item}")
    else:
        lines.append("  暂无重点事项")

    # 下周计划
    lines.append(f.section("下周计划", "📅"))
    if next_week_plan:
        for task in next_week_plan:
            p = task.get("priority", "P2")
            icon = f.priority_icon(p)
            status = "⏳" if task.get("status") == "in_progress" else "○"
            lines.append(f"  {status} {icon} {task.get('content', '')}")
    else:
        lines.append("  暂无计划任务")

    # AI 总结
    lines.append(f.section("AI 周总结", "🤖"))
    for sentence in ai_summary.split("。"):
        if sentence.strip():
            lines.append(f"  {sentence.strip()}。")

    report_text = "\n".join(lines)

    return report_text, report_data


def save_report(report: str) -> Path:
    """保存周报到文件"""
    WEEKLY_REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    monday, _, week_range = get_week_range()
    week_str = monday.strftime("%Y-W%W")
    report_file = WEEKLY_REPORTS_DIR / f"{week_str}.md"

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    return report_file


def log_message(message: str):
    """记录日志"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "cron.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] [WEEKLY] {message}\n")


def main():
    """主函数"""
    log_message("开始生成周报...")

    try:
        # 生成周报
        report_text, report_data = generate_weekly_report()

        # 保存报告
        report_file = save_report(report_text)
        log_message(f"周报已保存: {report_file}")

        # 发送 Telegram 通知
        sender = TelegramSender()
        if sender.is_configured():
            # 使用格式化后的消息发送
            result = sender.send(format_weekly_report(report_data))
            if result["success"]:
                log_message(f"Telegram 通知已发送 ({result['sent_count']} 条消息)")
            else:
                log_message(f"Telegram 发送失败: {result.get('error', '未知错误')}")

        # 输出到控制台
        print(report_text)

        log_message("周报生成完成")
        return 0

    except Exception as e:
        log_message(f"周报生成失败: {e}")
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
