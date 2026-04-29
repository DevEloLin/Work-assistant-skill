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

定时任务基于 UTC 时间执行，本地时间根据配置文件中的 `user.timezone` 自动转换显示。

| UTC 时间 | 任务 |
|----------|------|
| 05:30 | 每日晨报 |
| 06:00-15:00 | 每小时邮件检查 |
| 14:00 | 每日工作总结 |
| 06:30 (周五) | 周报生成 |
| 16:00-05:30 | 静默时间 |

> 配置时区示例：`timezone: "Asia/Shanghai"` (UTC+8), `timezone: "Asia/Dubai"` (UTC+4)

## 使用命令

在 Claude Code 或 OpenClaw 中使用：

```bash
# 任务管理
/work todo add "任务内容" -p P1 -d 2026-04-30
/work todo list
/work todo update <ID> -s done

# 邮件处理
/work email read -n 10
/work email summary
/work email sent -t today --analyze

# 工作汇报
/work report morning      # 晨报
/work report daily        # 日报（含邮件工作分析）
/work report weekly       # 周报（聚合本周日报）
/work summary             # 快速总结

# 系统
/work status
/work cron status
```

## 目录结构

```
miren-work-assistant-skill/
├── install.sh                 # 统一安装脚本
├── install-openclaw.sh        # OpenClaw 安装
├── install-claude-code.sh     # Claude Code 安装
├── PRD-v1.md                  # 产品需求文档
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
