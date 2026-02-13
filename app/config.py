"""
配置加载模块
支持多账号配置，每个账号可设置独立的 cron 表达式和 AI prompt
"""

import json
import os
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AccountConfig:
    """单个账号配置"""
    name: str                    # 账号名称（用于日志标识）
    from_email: str              # 发件人邮箱
    from_name: str               # 发件人名称
    to_email: str                # 收件人邮箱
    cron: str                    # cron 表达式（5位：分 时 日 月 周）
    ai_prompt: str               # AI 生成内容的 system prompt
    subject_prefix: str = ""     # 邮件主题前缀（可选）

    def __post_init__(self):
        """验证配置有效性"""
        required = ["name", "from_email", "to_email", "cron", "ai_prompt"]
        for field_name in required:
            if not getattr(self, field_name, "").strip():
                raise ValueError(f"账号配置缺少必填字段: {field_name}")

        # 验证 cron 格式（5位）
        parts = self.cron.strip().split()
        if len(parts) != 5:
            raise ValueError(
                f"[{self.name}] cron 表达式格式错误，需要 5 个字段 (分 时 日 月 周)，"
                f"当前为 {len(parts)} 个字段: '{self.cron}'"
            )


@dataclass
class AppConfig:
    """全局应用配置"""
    resend_api_key: str          # Resend API Key
    ai_api_key: str              # OpenAI 兼容 API Key
    ai_api_base: str             # API Base URL
    ai_model: str                # 模型名称
    accounts: list[AccountConfig] = field(default_factory=list)
    timezone: str = "Asia/Shanghai"  # 时区
    tg_bot_token: str = ""           # Telegram Bot Token（可选）
    tg_chat_id: str = ""             # Telegram Chat ID（可选）

    def __post_init__(self):
        if not self.resend_api_key:
            raise ValueError("缺少 RESEND_API_KEY 环境变量")
        if not self.ai_api_key:
            raise ValueError("缺少 AI_API_KEY 环境变量")
        if not self.accounts:
            raise ValueError("至少需要配置一个账号 (ACCOUNTS)")


def load_config() -> AppConfig:
    """从环境变量加载配置"""
    # 加载全局配置
    resend_api_key = os.environ.get("RESEND_API_KEY", "")
    ai_api_key = os.environ.get("AI_API_KEY", "")
    ai_api_base = os.environ.get("AI_API_BASE", "https://api.openai.com/v1")
    ai_model = os.environ.get("AI_MODEL", "gpt-4o-mini")
    timezone = os.environ.get("TZ", "Asia/Shanghai")
    tg_bot_token = os.environ.get("TG_BOT_TOKEN", "")
    tg_chat_id = os.environ.get("TG_CHAT_ID", "")

    # 加载账号配置（JSON 数组）
    accounts_json = os.environ.get("ACCOUNTS", "[]")
    try:
        accounts_raw = json.loads(accounts_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"ACCOUNTS 环境变量 JSON 解析失败: {e}")

    if not isinstance(accounts_raw, list):
        raise ValueError("ACCOUNTS 必须是 JSON 数组")

    accounts = []
    for i, acc in enumerate(accounts_raw):
        if not isinstance(acc, dict):
            raise ValueError(f"ACCOUNTS[{i}] 必须是 JSON 对象")
        try:
            accounts.append(AccountConfig(
                name=acc.get("name", f"account_{i}"),
                from_email=acc.get("from_email", ""),
                from_name=acc.get("from_name", ""),
                to_email=acc.get("to_email", ""),
                cron=acc.get("cron", ""),
                ai_prompt=acc.get("ai_prompt", ""),
                subject_prefix=acc.get("subject_prefix", ""),
            ))
        except ValueError as e:
            raise ValueError(f"ACCOUNTS[{i}] 配置错误: {e}")

    config = AppConfig(
        resend_api_key=resend_api_key,
        ai_api_key=ai_api_key,
        ai_api_base=ai_api_base,
        ai_model=ai_model,
        accounts=accounts,
        timezone=timezone,
        tg_bot_token=tg_bot_token,
        tg_chat_id=tg_chat_id,
    )

    logger.info(f"配置加载成功，共 {len(accounts)} 个账号:")
    for acc in accounts:
        logger.info(f"  - [{acc.name}] {acc.from_name}<{acc.from_email}> → {acc.to_email} | cron: {acc.cron}")

    return config
