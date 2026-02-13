# Auto-Sendmail 📧

使用 AI 生成拟人化的日常聊天邮件，通过 Resend API 定时自动发送。支持多账号配置，每个账号可设置独立的 cron 定时计划。

## ✨ 功能特性

- 🤖 **AI 拟人内容**：使用 OpenAI 兼容 API 生成自然的日常聊天邮件
- 📧 **Resend 发邮件**：通过 Resend API 可靠地发送邮件
- ⏰ **Cron 定时发送**：支持标准 cron 表达式灵活配置发送时间
- 👥 **多账号支持**：每个账号可配置不同的收件人、发送时间、AI 角色
- 🐳 **Docker 部署**：一键 Docker 部署，GitHub Actions 自动构建镜像

## 🚀 快速开始

### Docker 部署（推荐）

1. 创建配置文件：
```bash
cp .env.example .env
# 编辑 .env 填写你的配置
```

2. 启动服务：
```bash
docker-compose up -d
```

3. 查看日志：
```bash
docker-compose logs -f
```

### 本地运行

1. 创建虚拟环境并安装依赖：
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 填写你的配置
```

3. 运行：
```bash
python -m app.main
```

## ⚙️ 配置说明

### 全局配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `RESEND_API_KEY` | Resend API Key | 必填 |
| `AI_API_KEY` | OpenAI 兼容 API Key | 必填 |
| `AI_API_BASE` | API Base URL | `https://api.openai.com/v1` |
| `AI_MODEL` | 模型名称 | `gpt-4o-mini` |
| `TZ` | 时区 | `Asia/Shanghai` |
| `TG_BOT_TOKEN` | Telegram Bot Token（可选） | - |
| `TG_CHAT_ID` | Telegram Chat ID（可选） | - |
| `DEFAULT_EMAIL_DOMAIN` | 全局发件人域名，自动生成 `随机英文名@域名` | - |
| `DEFAULT_FROM_NAME` | 全局发件人名称，留空则自动生成 | - |
| `DEFAULT_AI_PROMPT` | 全局默认 AI Prompt | - |

### 账号配置

通过 `ACCOUNTS` 环境变量传入 JSON 数组，每个账号支持以下字段：

| 字段 | 说明 | 必填 |
|------|------|------|
| `name` | 账号名称（用于日志标识） | ✅ |
| `from_email` | 发件人邮箱（不填则使用全局域名自动生成） | 否 |
| `from_name` | 发件人显示名称（不填则自动生成或使用全局） | 否 |
| `to_email` | 收件人邮箱 | ✅ |
| `cron` | cron 表达式（分 时 日 月 周） | ✅ |
| `ai_prompt` | AI 角色和场景描述（不填则使用全局） | 否 |
| `subject_prefix` | 邮件主题前缀 | 否 |

### Cron 表达式示例

| 表达式 | 含义 |
|--------|------|
| `30 8 * * *` | 每天 8:30 |
| `0 9,21 * * *` | 每天 9:00 和 21:00 |
| `0 */2 * * *` | 每 2 小时 |
| `0 8 * * 1-5` | 工作日每天 8:00 |
| `0 20 1,15 * *` | 每月 1 号和 15 号 20:00 |

## 🔧 AI API 兼容性

支持任何 OpenAI 格式兼容的 API：

| 服务 | `AI_API_BASE` |
|------|---------------|
| OpenAI | `https://api.openai.com/v1` |
| DeepSeek | `https://api.deepseek.com` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| Ollama (本地) | `http://localhost:11434/v1` |

## 📝 License

MIT
