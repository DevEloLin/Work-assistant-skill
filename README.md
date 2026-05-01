# Miren Work Assistant

智能工作助手 Skill，支持 **Claude Code** 和 **OpenClaw**，提供：
- 自动化晨报与邮件监控
- 任务管理与工作规划
- 基于邮件的工作总结
- 工作汇报自动生成（日报/周报）
- Telegram 通知推送

## 快速安装

### 自动安装（推荐）

```bash
./install.sh
```

交互式选择安装到 Claude Code 或 OpenClaw。

### 命令行安装

```bash
# 安装到 OpenClaw
./install.sh --openclaw

# 安装到 Claude Code
./install.sh --claude-code

# 两者都安装
./install.sh --both
```

### 手动安装

#### OpenClaw

```bash
./install-openclaw.sh
```

Skill 将安装到 `~/.openclaw/workspace/skills/miren-work-assistant/`

#### Claude Code

```bash
./install-claude-code.sh
```

Skill 将安装到 `~/.claude/skills/miren-work-assistant/`

## 配置

### 1. 编辑配置文件

```bash
nano ~/.miren-work/config.yaml
```

主要配置项：
- `user.name` - 你的姓名
- `user.email` - 你的邮箱
- `user.timezone` - 你的时区 (如 `Asia/Shanghai`, `Asia/Dubai`, `America/New_York`)
- `notification.telegram` - Telegram 通知配置

### 2. 设置环境变量

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
```

### 3. 安装定时任务

```bash
~/.openclaw/workspace/skills/miren-work-assistant/scripts/cron_manager.sh install
# 或
~/.claude/skills/miren-work-assistant/scripts/cron_manager.sh install
```

## 定时任务

定时任务按用户配置的 **本地时区** 执行（`cron_manager.sh` 自动把本地时间转成 UTC cron 表达式写入系统 crontab）。

| 本地时间 | 任务 |
|----------|------|
| 08:30 | 每日晨报 |
| 09:00-18:00 每小时 | 邮件检查 |
| 18:00 | 每日工作总结 |
| 10:30 (周五) | 周报生成 |

> 配置时区示例：`timezone: "Asia/Shanghai"` (UTC+8)、`timezone: "Asia/Dubai"` (UTC+4)

## 使用方式（纯自然语言）

无需任何命令。直接在 Claude Code 或 OpenClaw 中说人话即可，Agent 会自动识别意图并触发本 skill 走对应流程。

```
晨报                  → 生成晨报
检查邮件 / 看邮件      → 检查最近邮件并更新 TODO
日报 / 工作总结       → 生成今日工作总结
周报 / 本周总结       → 生成本周周报
记一下: 修复登录 bug   → 添加任务 (默认 P2)
完成了 修复登录 bug    → 标记任务完成
待办 / 任务列表       → 列出当前待办
```

cron 注入的 prompt 也是同样的自然语言（见 `scripts/cron_manager.sh` 中的 `PROMPT_*`），不依赖任何斜杠命令语法。

## 目录结构

```
miren-work-assistant-skill/
├── install.sh                 # 统一安装脚本
├── install-openclaw.sh        # OpenClaw 安装
├── install-claude-code.sh     # Claude Code 安装
├── README.md                  # 说明文档
├── skills/
│   └── miren-work-assistant/
│       └── SKILL.md           # Skill 定义 (OpenClaw/Claude Code 通用)
├── scripts/
│   ├── init.sh                # 初始化脚本
│   └── cron_manager.sh        # Cron 管理 (直接调用 Agent CLI)
└── templates/
    └── config.yaml            # 配置模板

~/.miren-work/                 # 运行时数据目录
├── config.yaml                # 用户配置
└── data/
    ├── todos/                 # 待办任务
    ├── reports/               # 汇报存档
    │   ├── morning/
    │   ├── daily/
    │   └── weekly/
    ├── cache/                 # 缓存
    └── logs/                  # 日志
```

## SKILL.md 格式

本项目使用 [Agent Skills 规范](https://docs.openclaw.ai/tools/skills)，兼容：
- OpenClaw
- Claude Code
- Codex
- OpenAI Skills

## MCP 依赖

需要配置 `ms-365-mcp-server` 用于邮件读取：

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

## Telegram 通知

### 配置方式

1. 创建 Telegram Bot（通过 @BotFather）
2. 获取 Chat ID
3. 配置方式二选一：

**环境变量（推荐）：**
```bash
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
```

**配置文件：**
```yaml
# ~/.miren-work/config.yaml
notification:
  telegram:
    enabled: true
    bot_token: "YOUR_BOT_TOKEN"
    chat_id: "YOUR_CHAT_ID"
```

### 消息格式

- HTML 标签格式化
- 进度条可视化 `████████░░ 80%`
- 优先级/状态图标
- 智能消息分割（避免断层）

## 手动执行

```bash
# 晨报
./scripts/cron_manager.sh run morning

# 邮件检查
./scripts/cron_manager.sh run email

# 日报
./scripts/cron_manager.sh run summary

# 周报
./scripts/cron_manager.sh run weekly
```

## 许可证

MIT License
