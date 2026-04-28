#!/usr/bin/env python3
"""
Telegram 消息格式化模块
确保消息美观、清晰、完整发送
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

# Telegram 消息限制
MAX_MESSAGE_LENGTH = 4096
SAFE_MESSAGE_LENGTH = 4000  # 留出安全边界


@dataclass
class TelegramConfig:
    """Telegram 配置"""
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""


def load_telegram_config() -> TelegramConfig:
    """加载 Telegram 配置"""
    config_file = Path.home() / ".miren-work" / "config.yaml"

    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            tg_config = config.get("notification", {}).get("telegram", {})

            return TelegramConfig(
                enabled=tg_config.get("enabled", False),
                bot_token=os.environ.get("TELEGRAM_BOT_TOKEN") or tg_config.get("bot_token", ""),
                chat_id=tg_config.get("chat_id", "")
            )

    return TelegramConfig()


class TelegramFormatter:
    """Telegram 消息格式化器"""

    # 分隔线样式
    DIVIDER_THICK = "━" * 28
    DIVIDER_THIN = "─" * 28
    DIVIDER_DOT = "┄" * 28

    @staticmethod
    def header(title: str, emoji: str = "") -> str:
        """生成标题头"""
        if emoji:
            return f"{emoji} <b>{title}</b>"
        return f"<b>{title}</b>"

    @staticmethod
    def section(title: str, emoji: str = "📌") -> str:
        """生成章节标题"""
        return f"\n{emoji} <b>{title}</b>\n{TelegramFormatter.DIVIDER_THIN}"

    @staticmethod
    def subsection(title: str) -> str:
        """生成子章节标题"""
        return f"\n<b>▸ {title}</b>"

    @staticmethod
    def bullet_list(items: List[str], indent: int = 0) -> str:
        """生成项目符号列表"""
        if not items:
            return f"{'  ' * indent}  <i>暂无</i>"

        prefix = "  " * indent
        lines = []
        for item in items:
            lines.append(f"{prefix}• {item}")
        return "\n".join(lines)

    @staticmethod
    def numbered_list(items: List[str], indent: int = 0) -> str:
        """生成编号列表"""
        if not items:
            return f"{'  ' * indent}  <i>暂无</i>"

        prefix = "  " * indent
        lines = []
        for i, item in enumerate(items, 1):
            lines.append(f"{prefix}{i}. {item}")
        return "\n".join(lines)

    @staticmethod
    def status_item(label: str, value: str, status: str = "✅") -> str:
        """生成状态项"""
        return f"  {status} {label}: {value}"

    @staticmethod
    def key_value(key: str, value: Any, indent: int = 0) -> str:
        """生成键值对"""
        prefix = "  " * indent
        return f"{prefix}<b>{key}:</b> {value}"

    @staticmethod
    def progress_bar(current: int, total: int, width: int = 10) -> str:
        """生成进度条"""
        if total == 0:
            return "░" * width + " 0%"

        percent = int(current / total * 100)
        filled = int(width * current / total)
        bar = "█" * filled + "░" * (width - filled)
        return f"{bar} {percent}%"

    @staticmethod
    def table_row(cols: List[str], widths: Optional[List[int]] = None) -> str:
        """生成表格行（使用等宽字符对齐）"""
        if widths is None:
            return " │ ".join(cols)

        formatted = []
        for col, width in zip(cols, widths):
            # 使用 ljust 进行对齐
            formatted.append(str(col).ljust(width))
        return " │ ".join(formatted)

    @staticmethod
    def code_block(text: str) -> str:
        """生成代码块"""
        return f"<code>{text}</code>"

    @staticmethod
    def bold(text: str) -> str:
        """加粗文本"""
        return f"<b>{text}</b>"

    @staticmethod
    def italic(text: str) -> str:
        """斜体文本"""
        return f"<i>{text}</i>"

    @staticmethod
    def highlight(text: str) -> str:
        """高亮文本"""
        return f"<b>{text}</b>"

    @staticmethod
    def priority_icon(priority: str) -> str:
        """获取优先级图标"""
        icons = {
            "P0": "🔴",
            "P1": "🟠",
            "P2": "🟡",
            "P3": "🟢"
        }
        return icons.get(priority, "⚪")

    @staticmethod
    def status_icon(status: str) -> str:
        """获取状态图标"""
        icons = {
            "done": "✅",
            "completed": "✅",
            "in_progress": "⏳",
            "pending": "○",
            "blocked": "🚫",
            "cancelled": "❌",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }
        return icons.get(status, "•")

    @staticmethod
    def work_type_icon(work_type: str) -> str:
        """获取工作类型图标"""
        icons = {
            "工单处理": "🎫",
            "代码审查": "👀",
            "会议沟通": "💬",
            "报告撰写": "📝",
            "部署运维": "🚀",
            "团队协作": "👥",
            "日常沟通": "💭"
        }
        return icons.get(work_type, "📧")


class TelegramSender:
    """Telegram 消息发送器"""

    def __init__(self, config: Optional[TelegramConfig] = None):
        self.config = config or load_telegram_config()
        self.formatter = TelegramFormatter()

    def is_configured(self) -> bool:
        """检查是否已配置"""
        return (
            self.config.enabled and
            self.config.bot_token and
            self.config.chat_id and
            self.config.chat_id != "YOUR_CHAT_ID"
        )

    def _split_message(self, message: str) -> List[str]:
        """
        智能分割长消息，确保不会在不恰当的位置断开
        """
        if len(message) <= SAFE_MESSAGE_LENGTH:
            return [message]

        messages = []
        lines = message.split('\n')
        current_chunk = []
        current_length = 0

        for line in lines:
            line_length = len(line) + 1  # +1 for newline

            # 如果单行超长，需要强制截断
            if line_length > SAFE_MESSAGE_LENGTH:
                # 先保存当前块
                if current_chunk:
                    messages.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0

                # 截断长行
                while len(line) > SAFE_MESSAGE_LENGTH:
                    messages.append(line[:SAFE_MESSAGE_LENGTH])
                    line = line[SAFE_MESSAGE_LENGTH:]

                if line:
                    current_chunk.append(line)
                    current_length = len(line) + 1

            # 如果添加这行会超出限制
            elif current_length + line_length > SAFE_MESSAGE_LENGTH:
                # 保存当前块并开始新块
                messages.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = line_length

            else:
                current_chunk.append(line)
                current_length += line_length

        # 保存最后一块
        if current_chunk:
            messages.append('\n'.join(current_chunk))

        return messages

    def send(self, message: str, parse_mode: str = "HTML") -> Dict[str, Any]:
        """
        发送消息，自动处理长消息分割
        返回发送结果
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "Telegram 未配置或未启用",
                "sent_count": 0
            }

        try:
            import requests
        except ImportError:
            return {
                "success": False,
                "error": "requests 模块未安装",
                "sent_count": 0
            }

        # 分割消息
        message_parts = self._split_message(message)
        total_parts = len(message_parts)

        results = []
        for i, part in enumerate(message_parts, 1):
            # 如果有多个部分，添加序号标识
            if total_parts > 1:
                part = f"[{i}/{total_parts}]\n{part}"

            try:
                url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"
                data = {
                    "chat_id": self.config.chat_id,
                    "text": part,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True  # 禁用链接预览
                }

                response = requests.post(url, json=data, timeout=30)
                result = response.json()

                if not result.get("ok"):
                    return {
                        "success": False,
                        "error": result.get("description", "发送失败"),
                        "sent_count": i - 1
                    }

                results.append(result)

            except requests.exceptions.Timeout:
                return {
                    "success": False,
                    "error": f"发送超时 (第 {i}/{total_parts} 部分)",
                    "sent_count": i - 1
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"发送错误: {str(e)}",
                    "sent_count": i - 1
                }

        return {
            "success": True,
            "sent_count": total_parts,
            "results": results
        }


def format_morning_report(data: Dict) -> str:
    """格式化晨报消息"""
    f = TelegramFormatter

    today = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    weekday = data.get("weekday", "")

    lines = [
        f.header(f"每日晨报 - {today} {weekday}", "🌅"),
        "",
        f.section("系统状态", "📊"),
    ]

    # 系统状态
    status = data.get("system_status", {})
    for name, state in status.items():
        icon = f.status_icon("success" if "正常" in state or "已连接" in state else "warning")
        lines.append(f"  {icon} {name}: {state}")

    # 今日待办
    lines.append(f.section("今日待办任务", "📋"))

    todos = data.get("todos_by_priority", {})
    priority_names = {"P0": "紧急重要", "P1": "重要", "P2": "一般", "P3": "低优先级"}

    for p in ["P0", "P1", "P2", "P3"]:
        tasks = todos.get(p, [])
        icon = f.priority_icon(p)
        lines.append(f"\n{icon} <b>{p} {priority_names[p]}</b>")

        if tasks:
            for task in tasks[:5]:  # 最多显示5个
                status_icon = "⏳" if task.get("status") == "in_progress" else "○"
                due = task.get("due_date", "")
                due_str = f" <i>(截止: {due})</i>" if due else ""
                lines.append(f"  {status_icon} {task['content']}{due_str}")
        else:
            lines.append(f"  <i>无</i>")

    # 待办统计
    lines.append(f.section("历史待办统计", "📈"))
    stats = data.get("stats", {})
    lines.append(f"  完成率: {stats.get('completion_rate', 'N/A')}")
    lines.append(f"  按优先级: {stats.get('priority_stats', 'N/A')}")
    lines.append(f"  按类型: {stats.get('type_stats', 'N/A')}")

    # 邮件摘要
    lines.append(f.section("过去24小时邮件", "📧"))
    email = data.get("email_summary", {})
    lines.append(f"  新收: {email.get('new_emails', 0)}封")
    lines.append(f"  未读: {email.get('unread_emails', 0)}封")
    lines.append(f"  重要: {email.get('important_emails', 0)}封")
    lines.append(f"  需回复: {email.get('need_reply', 0)}封")

    important_list = data.get("important_emails", [])
    if important_list:
        lines.append(f"\n<b>重要邮件:</b>")
        for i, mail in enumerate(important_list[:5], 1):
            lines.append(f"  {i}. [{mail.get('reason', '')}] {mail.get('subject', '')}")

    # 重要提醒
    reminders = data.get("reminders", [])
    if reminders:
        lines.append(f.section("重要提醒", "⚠️"))
        for reminder in reminders:
            lines.append(f"  • {reminder}")

    return "\n".join(lines)


def format_email_alert(data: Dict) -> str:
    """格式化邮件告警消息"""
    f = TelegramFormatter

    now = datetime.now().strftime("%H:%M")
    important_count = len(data.get("important_emails", []))

    lines = [
        f.header(f"邮件检查 ({now})", "📧"),
        "",
        f"发现 <b>{important_count}</b> 封重要邮件:",
        f.DIVIDER_THIN,
    ]

    for i, email in enumerate(data.get("important_emails", []), 1):
        reason = email.get("reason", "")
        subject = email.get("subject", "无主题")
        sender = email.get("from", "")
        time = email.get("time", "")

        lines.append(f"\n<b>{i}. [{reason}]</b>")
        lines.append(f"   {subject}")
        if sender:
            lines.append(f"   <i>发件人: {sender}</i>")
        if time:
            lines.append(f"   <i>时间: {time}</i>")

    return "\n".join(lines)


def format_daily_summary(data: Dict) -> str:
    """格式化每日工作总结消息"""
    f = TelegramFormatter

    today = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    weekday = data.get("weekday", "")

    lines = [
        f.header(f"每日工作总结 - {today} {weekday}", "📊"),
        "",
    ]

    # 邮件工作统计
    lines.append(f.section("邮件工作统计", "📧"))

    email_stats = data.get("email_analysis", {})
    total = email_stats.get("total", 0)
    lines.append(f"  发送邮件: <b>{total}</b> 封")

    by_type = email_stats.get("by_type", {})
    if by_type:
        lines.append("")
        for work_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
            icon = f.work_type_icon(work_type)
            percent = int(count / total * 100) if total > 0 else 0
            bar = f.progress_bar(count, total, 8)
            lines.append(f"  {icon} {work_type}: {bar} ({count}封)")

    # 工作明细
    details = data.get("work_details", [])
    if details:
        lines.append(f.section("工作明细", "📋"))
        for item in details[:8]:
            icon = f.work_type_icon(item.get("type", ""))
            lines.append(f"  {icon} {item.get('subject', '')}")
        if len(details) > 8:
            lines.append(f"  <i>... 还有 {len(details) - 8} 项</i>")

    # 已完成任务
    completed = data.get("completed_todos", [])
    lines.append(f.section(f"已完成任务 ({len(completed)}项)", "✅"))
    if completed:
        for task in completed[:5]:
            p = task.get("priority", "P2")
            icon = f.priority_icon(p)
            lines.append(f"  {icon} {task.get('content', '')}")
        if len(completed) > 5:
            lines.append(f"  <i>... 还有 {len(completed) - 5} 项</i>")
    else:
        lines.append(f"  <i>暂无完成的任务</i>")

    # AI 总结
    ai_summary = data.get("ai_summary", "")
    if ai_summary:
        lines.append(f.section("AI 总结", "🤖"))
        lines.append(f"  {ai_summary}")

    # 明日计划
    tomorrow = data.get("tomorrow_plan", [])
    if tomorrow:
        lines.append(f.section("明日计划", "📅"))
        for task in tomorrow[:5]:
            p = task.get("priority", "P2")
            icon = f.priority_icon(p)
            status = "⏳" if task.get("status") == "in_progress" else "○"
            lines.append(f"  {status} {icon} {task.get('content', '')}")

    return "\n".join(lines)


def format_weekly_report(data: Dict) -> str:
    """格式化周报消息"""
    f = TelegramFormatter

    week_range = data.get("week_range", "")

    lines = [
        f.header(f"本周工作总结 - {week_range}", "📊"),
        "",
    ]

    # 工作概览
    lines.append(f.section("工作概览", "📈"))
    overview = data.get("overview", {})
    lines.append(f"  📧 发送邮件: <b>{overview.get('total_emails', 0)}</b> 封")
    lines.append(f"  ✅ 完成任务: <b>{overview.get('completed_tasks', 0)}</b> 项")
    lines.append(f"  📊 完成率: <b>{overview.get('completion_rate', 'N/A')}</b>")

    # 工作分布
    lines.append(f.section("工作分布", "📋"))
    work_dist = data.get("work_distribution", {})
    if work_dist:
        total = sum(work_dist.values())
        for work_type, count in sorted(work_dist.items(), key=lambda x: -x[1]):
            icon = f.work_type_icon(work_type)
            bar = f.progress_bar(count, total, 8)
            lines.append(f"  {icon} {work_type}: {bar} ({count})")

    # 每日统计
    lines.append(f.section("每日工作量", "📆"))
    daily_stats = data.get("daily_stats", [])
    for day in daily_stats:
        date = day.get("date", "")
        weekday = day.get("weekday", "")
        emails = day.get("emails", 0)
        tasks = day.get("tasks", 0)
        bar = f.progress_bar(emails, 20, 6)  # 假设日最大20封
        lines.append(f"  {weekday} ({date}): {bar} 📧{emails} ✅{tasks}")

    # 重点完成
    lines.append(f.section("本周重点完成", "🎯"))
    highlights = data.get("highlights", [])
    if highlights:
        for i, item in enumerate(highlights[:6], 1):
            lines.append(f"  {i}. {item}")
    else:
        lines.append(f"  <i>暂无重点事项</i>")

    # 下周计划
    lines.append(f.section("下周计划", "📅"))
    next_week = data.get("next_week_plan", [])
    if next_week:
        for task in next_week[:5]:
            p = task.get("priority", "P2")
            icon = f.priority_icon(p)
            lines.append(f"  {icon} {task.get('content', '')}")
    else:
        lines.append(f"  <i>暂无计划任务</i>")

    # AI 周总结
    ai_summary = data.get("ai_summary", "")
    if ai_summary:
        lines.append(f.section("AI 周总结", "🤖"))
        # 分行显示长总结
        for line in ai_summary.split("。"):
            if line.strip():
                lines.append(f"  {line.strip()}。")

    return "\n".join(lines)


# 便捷发送函数
def send_morning_report(data: Dict) -> Dict:
    """发送晨报"""
    sender = TelegramSender()
    message = format_morning_report(data)
    return sender.send(message)


def send_email_alert(data: Dict) -> Dict:
    """发送邮件告警"""
    sender = TelegramSender()
    message = format_email_alert(data)
    return sender.send(message)


def send_daily_summary(data: Dict) -> Dict:
    """发送每日总结"""
    sender = TelegramSender()
    message = format_daily_summary(data)
    return sender.send(message)


def send_weekly_report(data: Dict) -> Dict:
    """发送周报"""
    sender = TelegramSender()
    message = format_weekly_report(data)
    return sender.send(message)


if __name__ == "__main__":
    # 测试格式化
    test_data = {
        "date": "2026-04-28",
        "weekday": "周二",
        "system_status": {
            "AI 助理": "✅ 正常",
            "MS365 邮箱": "✅ 已连接",
            "Telegram": "✅ 已连接",
            "Cron 任务": "✅ 运行中"
        },
        "todos_by_priority": {
            "P0": [],
            "P1": [{"content": "完成PRD文档", "status": "in_progress", "due_date": "2026-04-28"}],
            "P2": [{"content": "代码审查", "status": "pending"}],
            "P3": []
        },
        "stats": {
            "completion_rate": "75% (15/20)",
            "priority_stats": "P0:0 P1:5 P2:10 P3:5",
            "type_stats": "开发:8 会议:5 文档:4"
        },
        "email_summary": {
            "new_emails": 12,
            "unread_emails": 5,
            "important_emails": 2,
            "need_reply": 3
        }
    }

    print(format_morning_report(test_data))
