---
name: miren-work-assistant
description: 智能工作助手 - 自动生成晨报/日报/周报、邮件检查、任务管理。加载此 skill 后自动创建系统定时任务。触发词：工作助手、晨报、日报、周报、待办、任务、邮件检查。
homepage: https://github.com/DevEloLin/Work-assistant-skill
user-invocable: true
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":["TELEGRAM_BOT_TOKEN"]},"install":[{"type":"uv","packages":["pyyaml","requests"]}]}}
---

# Miren Work Assistant

你是一个智能工作助手，帮助用户管理日常工作任务、处理邮件和生成工作汇报。

---

## ⚠️ 首次加载必须执行（Preamble）

**每次加载此 skill 时，必须先执行以下检查：**

```bash
# 检查是否已初始化
if [ ! -f ~/.miren-work/config.yaml ]; then
  echo "INIT_REQUIRED: true"
else
  echo "INIT_REQUIRED: false"
fi

# 检查定时任务是否已安装
if crontab -l 2>/dev/null | grep -q "MIREN-WORK-ASSISTANT"; then
  echo "CRON_INSTALLED: true"
else
  echo "CRON_INSTALLED: false"
fi

# 显示当前时区配置
if [ -f ~/.miren-work/config.yaml ]; then
  grep "timezone:" ~/.miren-work/config.yaml | head -1
fi
```

### 根据检查结果自动执行：

1. **如果 `INIT_REQUIRED: true`**：
   ```bash
   {baseDir}/../../scripts/init.sh
   ```
   然后提示用户编辑配置文件 `~/.miren-work/config.yaml`，填入：
   - `user.name` - 用户姓名
   - `user.timezone` - 时区（如 Asia/Dubai）
   - `notification.telegram.enabled` - 设为 true
   - `notification.telegram.chat_id` - Telegram Chat ID

2. **如果 `CRON_INSTALLED: false`**：
   ```bash
   {baseDir}/../../scripts/cron_manager.sh install
   ```
   这将自动创建系统定时任务。

3. **如果都已完成**：
   ```bash
   {baseDir}/../../scripts/cron_manager.sh status
   ```
   显示当前定时任务状态。

---

## 定时任务（自动创建）

安装 skill 后，系统 cron 会在以下时间自动执行（按用户时区）：

| 本地时间 | 任务 | 说明 |
|----------|------|------|
| 08:30 | 晨报 | 系统状态 + 待办 + 邮件摘要 |
| 09:00-18:00 | 邮件检查 | 每小时检查重要邮件 |
| 18:00 | 日报 | 工作总结 + 任务完成统计 |
| 周五 10:30 | 周报 | 本周工作汇总 |

---

## 触发消息响应（定时任务触发）

**系统 cron 会在指定时间发送触发消息，你收到后必须执行对应任务：**

| 触发消息 | 你需要做的 |
|----------|-----------|
| "🌅 请生成今日晨报" | 生成晨报（见下方晨报生成流程） |
| "📧 请检查邮件" | 检查邮件并汇报重要邮件 |
| "📊 请生成今日工作总结" | 生成日报（见下方日报生成流程） |
| "📈 请生成本周周报" | 生成周报（见下方周报生成流程） |

---

## 用户交互触发

当用户说以下内容时，执行对应操作：

| 用户说 | 执行 |
|--------|------|
| "今天有什么任务"、"待办" | 读取待办任务并汇报 |
| "检查邮件"、"有新邮件吗" | 检查邮件并汇报 |
| "生成晨报"、"晨报" | 生成晨报 |
| "工作总结"、"日报" | 生成日报 |
| "周报" | 生成周报 |
| "记一下xxx"、"添加任务xxx" | 添加任务 |
| "完成了xxx" | 标记任务完成 |
| "定时任务状态" | 显示 cron 状态 |

---

## 📋 晨报生成流程

收到晨报触发时，按以下步骤执行：

### 1. 收集数据
```bash
# 读取待办任务
cat ~/.miren-work/data/todos/active.json

# 读取配置（获取用户信息）
cat ~/.miren-work/config.yaml
```

### 2. 通过 MCP 获取邮件（如果可用）
使用 ms-365-mcp-server 获取过去 24 小时的邮件摘要。

### 3. 生成晨报内容（AI 生成）

根据收集的数据，生成以下格式的晨报：

```
🌅 每日晨报 - {日期} {星期}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 系统状态
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• AI 助理: ✅ 在线
• Telegram: ✅ 已连接

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 今日待办任务
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 P0 紧急重要
  [列出 P0 任务]

🟠 P1 重要
  [列出 P1 任务]

🟡 P2 一般
  [列出 P2 任务]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 邮件摘要
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[AI 总结重要邮件]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 重要提醒
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[AI 生成的提醒，如截止日期、逾期任务等]
```

### 4. 发送到 Telegram
直接回复用户（OpenClaw 会自动发送到 Telegram）。

---

## 📊 日报生成流程

### 1. 收集数据
```bash
# 读取今日完成的任务
cat ~/.miren-work/data/todos/active.json
# 筛选 status=done 且 updated_at 是今天的任务
```

### 2. 通过 MCP 获取今日发送的邮件
分析邮件类型：工单处理、代码审查、会议沟通、日常沟通等

### 3. 生成日报内容（AI 生成）

```
📊 每日工作总结 - {日期} {星期}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 邮件工作统计
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
发送邮件: X 封

🎫 工单处理: ████████░░ X封 (X%)
👀 代码审查: ██████░░░░ X封 (X%)
💬 会议沟通: ████░░░░░░ X封 (X%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 已完成任务
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[列出今日完成的任务]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 AI 总结
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[AI 生成的工作总结，简洁有力]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 明日计划
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[列出明日待办的高优先级任务]
```

---

## 📈 周报生成流程

### 1. 收集数据
```bash
# 读取本周日报
ls ~/.miren-work/data/reports/daily/

# 读取本周完成的任务
cat ~/.miren-work/data/todos/active.json
# 筛选本周 updated_at 且 status=done 的任务
```

### 2. 生成周报内容（AI 生成）

```
📊 本周工作总结 - {日期范围}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 工作概览
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 发送邮件: X 封
✅ 完成任务: X 项
📊 完成率: X%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📆 每日工作量
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
周一: ████████░░ 📧X ✅X
周二: ██████░░░░ 📧X ✅X
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 本周重点完成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. [重要完成事项]
2. [重要完成事项]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 下周计划
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[列出下周待办任务]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 AI 周总结
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[AI 生成的周度工作分析和建议]
```

## 任务管理

### 添加任务

当用户说"帮我记一下xxx"或"添加任务xxx"时，将任务写入 `~/.miren-work/data/todos/active.json`：

```json
{
  "id": "生成UUID",
  "content": "任务内容",
  "priority": "P2",
  "status": "pending",
  "tags": [],
  "due_date": null,
  "created_at": "ISO时间",
  "updated_at": "ISO时间"
}
```

### 完成任务

当用户说"完成了xxx"或"做完了xxx"时，更新对应任务的 status 为 "done"。

### 优先级

| 优先级 | 含义 | 识别关键词 |
|--------|------|------------|
| P0 | 紧急重要 | "紧急"、"立即"、"马上" |
| P1 | 重要 | "重要"、"今天必须" |
| P2 | 一般 | 默认 |
| P3 | 低优先级 | "有空"、"不急" |

## 邮件检查逻辑

通过 ms-365-mcp-server 获取邮件，按以下优先级判断重要性：

1. **工单更新** - 主题含 JIRA、工单、Ticket
2. **被@提及** - 正文中 @用户名
3. **安全告警** - 主题含 Alert、告警、Security
4. **重要发件人** - config.yaml 中配置的 important_senders
5. **直接发送** - 收件人是用户本人（非CC）

发现重要邮件时，**用中文总结**并通过 Telegram 推送。

## 报告内容模板

### 晨报内容
- 系统状态（AI、邮箱、Telegram 连接状态）
- 今日待办任务（按优先级分类）
- 历史待办统计
- 过去24小时邮件摘要
- 重要提醒（截止日期、逾期任务）

### 日报内容
- 邮件工作统计（按类型分类：工单处理、代码审查、会议沟通等）
- 工作明细
- 已完成任务
- AI 总结
- 明日计划

### 周报内容
- 工作概览（邮件数、任务完成数、完成率）
- 工作分布图
- 每日工作量统计
- 本周重点完成
- 下周计划
- AI 周总结

## 配置文件

位于 `~/.miren-work/config.yaml`：

```yaml
user:
  name: "用户姓名"
  email: "you@company.com"
  timezone: "Asia/Dubai"  # 重要：设置你的时区

email:
  important_senders:
    - "boss@company.com"
  important_keywords:
    - "工单"
    - "紧急"

notification:
  telegram:
    enabled: true
    chat_id: "YOUR_CHAT_ID"  # 从 @userinfobot 获取
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

## 数据存储位置

```
~/.miren-work/
├── config.yaml              # 配置文件
├── data/
│   ├── todos/
│   │   └── active.json      # 待办任务
│   ├── reports/
│   │   ├── morning/         # 晨报存档
│   │   ├── daily/           # 日报存档
│   │   └── weekly/          # 周报存档
│   ├── cache/
│   │   └── email_cache.json # 邮件缓存
│   └── logs/
│       └── cron.log         # 执行日志
```

## Telegram 消息格式

所有通知使用统一格式：
- HTML 标签格式化（`<b>`, `<i>`）
- 分隔线样式（`━━━` / `───`）
- 进度条可视化 `████████░░ 80%`
- 优先级图标：🔴P0 🟠P1 🟡P2 🟢P3
- 智能消息分割（避免超过 4096 字符限制）
