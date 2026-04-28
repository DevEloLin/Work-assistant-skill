---
name: miren-work-assistant
description: 智能工作助手 - 管理待办任务、邮件处理、生成晨报/日报/周报，支持 Telegram 通知推送
homepage: https://github.com/miren/work-assistant
user-invocable: true
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":["TELEGRAM_BOT_TOKEN"]},"install":[{"type":"uv","packages":["pyyaml","requests"]}]}}
---

# Miren Work Assistant

你是一个智能工作助手，帮助用户管理日常工作任务、处理邮件和生成工作汇报。

## 触发条件

当用户提到以下内容时激活此 skill：
- `/work` 命令
- 待办、任务、todo
- 晨报、日报、周报
- 邮件检查、邮件总结
- 工作总结、工作汇报

## 可用命令

### 定时任务管理
| 命令 | 说明 |
|------|------|
| `/work cron status` | 查看定时任务状态 |
| `/work cron start` | 启动定时任务 |
| `/work cron stop` | 停止定时任务 |

### 晨报相关
| 命令 | 说明 |
|------|------|
| `/work report morning` | 手动生成晨报 |
| `/work morning preview` | 预览晨报内容 |

### 邮件处理
| 命令 | 说明 |
|------|------|
| `/work email check` | 立即检查邮件 |
| `/work email read [-n 数量] [-u]` | 读取邮件列表 |
| `/work email summary [邮件ID]` | 生成邮件摘要 |
| `/work email sent -t today` | 分析今日发送的邮件 |

### 任务管理
| 命令 | 说明 |
|------|------|
| `/work todo add <内容> [-p P0-P3] [-d 日期]` | 添加任务 |
| `/work todo list [-s 状态] [-p 优先级]` | 查看任务列表 |
| `/work todo update <ID> [-s 状态]` | 更新任务 |
| `/work todo done <ID>` | 标记完成 |

### 工作汇报
| 命令 | 说明 |
|------|------|
| `/work report daily` | 生成日报（含邮件工作分析） |
| `/work report weekly` | 生成周报（聚合本周日报） |
| `/work summary` | 快速生成工作总结 |

### 系统
| 命令 | 说明 |
|------|------|
| `/work status` | 查看系统状态 |
| `/work config` | 查看/编辑配置 |

## 执行脚本

本 skill 包含以下可执行脚本，位于 `{baseDir}/../../scripts/`：

| 脚本 | 用途 |
|------|------|
| `morning_report.py` | 生成每日晨报 |
| `email_check.py` | 检查重要邮件 |
| `daily_summary.py` | 生成每日工作总结 |
| `weekly_report.py` | 生成周报 |
| `cron_manager.sh` | 管理定时任务 |
| `init.sh` | 初始化配置 |

## 执行指南

### 初始化设置

首次使用时运行初始化：

```bash
cd {baseDir}/../../scripts
./init.sh
```

这将创建：
- `~/.miren-work/config.yaml` - 配置文件
- `~/.miren-work/data/` - 数据目录

### 生成晨报

1. 读取配置文件 `~/.miren-work/config.yaml`
2. 检查系统状态（MCP 服务器连接）
3. 读取待办任务 `~/.miren-work/data/todos/active.json`
4. 通过 ms-365-mcp-server 获取邮件
5. 按照晨报模板生成内容
6. 通过 Telegram 发送通知

执行命令：
```bash
python3 {baseDir}/../../scripts/morning_report.py
```

### 生成日报

1. 读取 ms-365-mcp-server 获取今日发送的邮件
2. 按工作类型分类（工单/代码审查/会议/沟通）
3. 读取今日完成的任务
4. AI 生成工作总结
5. 发送 Telegram 通知

执行命令：
```bash
python3 {baseDir}/../../scripts/daily_summary.py
```

### 生成周报

1. 读取本周所有日报 (`~/.miren-work/data/reports/daily/`)
2. 聚合邮件统计、工作类型分布
3. 提取重点完成事项
4. AI 生成周总结
5. 发送 Telegram 通知

执行命令：
```bash
python3 {baseDir}/../../scripts/weekly_report.py
```

### 管理任务

任务数据结构：
```json
{
  "id": "uuid",
  "content": "任务内容",
  "priority": "P0|P1|P2|P3",
  "status": "pending|in_progress|done|blocked|cancelled",
  "tags": ["标签"],
  "due_date": "2026-04-30",
  "created_at": "2026-04-28T10:00:00Z",
  "updated_at": "2026-04-28T10:00:00Z"
}
```

任务存储位置：`~/.miren-work/data/todos/active.json`

## 定时任务时间表

定时任务根据用户配置的时区执行（`~/.miren-work/config.yaml` 中的 `user.timezone`）。

| 本地时间 | 任务 |
|----------|------|
| 08:30 | 每日晨报 |
| 09:00-18:00 | 每小时邮件检查 |
| 18:00 | 每日工作总结（日报） |
| 10:30 (周五) | 周报生成 |

> cron_manager.sh 会自动读取用户时区配置，将本地时间转换为系统 cron 所需的时间

安装定时任务：
```bash
{baseDir}/../../scripts/cron_manager.sh install
```

## 邮件重要性判断

按以下优先级筛选重要邮件：

1. **工单更新** - 主题含 JIRA、工单、Ticket
2. **被@提及** - 正文中 @用户名
3. **安全告警** - 主题含 Alert、告警、Security
4. **重要发件人** - config.yaml 中配置的 important_senders
5. **直接发送** - 收件人是用户本人（非CC）

## 优先级定义

| 优先级 | 图标 | 含义 | 处理时限 |
|--------|------|------|----------|
| P0 | 🔴 | 紧急重要 | 立即处理 |
| P1 | 🟠 | 重要 | 当日完成 |
| P2 | 🟡 | 一般 | 本周完成 |
| P3 | 🟢 | 低优先级 | 有空处理 |

## 配置文件

配置位于 `~/.miren-work/config.yaml`：

```yaml
user:
  name: "用户姓名"
  email: "you@company.com"
  timezone: "Asia/Shanghai"  # 用户所在时区 (如: Asia/Dubai, America/New_York)

email:
  important_senders:
    - "boss@company.com"
  important_keywords:
    - "工单"
    - "紧急"

notification:
  telegram:
    enabled: true
    chat_id: "YOUR_CHAT_ID"
```

## MCP 依赖

需要配置 ms-365-mcp-server 用于邮件读取：

```json
{
  "mcpServers": {
    "ms-365": {
      "command": "npx",
      "args": ["-y", "ms-365-mcp-server"]
    }
  }
}
```

## Telegram 消息格式

所有通知使用统一格式：
- HTML 标签格式化（`<b>`, `<i>`）
- 分隔线样式（`━━━` / `───`）
- 进度条可视化 `████████░░ 80%`
- 优先级/状态图标映射
- 智能消息分割（避免断层）
