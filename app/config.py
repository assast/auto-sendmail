"""
配置加载模块
支持多账号配置，每个账号可设置独立的 cron 表达式和 AI prompt
支持全局默认值：from_email（自动生成人名+域名）、from_name（自动生成）、ai_prompt
"""

import json
import os
import random
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# 常见英文名，用于自动生成发件人
FIRST_NAMES = [
    "James", "John", "Robert", "Michael", "David", "William", "Richard", "Joseph",
    "Thomas", "Charles", "Mary", "Patricia", "Jennifer", "Linda", "Barbara",
    "Elizabeth", "Susan", "Jessica", "Sarah", "Karen", "Emily", "Emma", "Olivia",
    "Sophia", "Isabella", "Daniel", "Matthew", "Anthony", "Mark", "Steven",
    "Andrew", "Paul", "Joshua", "Kenneth", "Kevin", "Brian", "George", "Timothy",
    "Ronald", "Edward", "Jason", "Jeffrey", "Ryan", "Jacob", "Nicholas",
    "Alice", "Grace", "Chloe", "Lily", "Hannah", "Mia", "Ella", "Charlotte",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White",
    "Harris", "Clark", "Lewis", "Robinson", "Walker", "Young", "Allen",
    "King", "Wright", "Scott", "Torres", "Hill", "Adams", "Nelson", "Baker",
    "Carter", "Mitchell", "Roberts", "Turner", "Phillips", "Campbell", "Parker",
]


def _generate_name() -> tuple[str, str]:
    """生成一个随机英文人名，返回 (first_name, full_name)"""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return first.lower(), f"{first} {last}"


def _generate_email(domain: str) -> tuple[str, str]:
    """
    自动生成发件人邮箱和人名
    返回 (email, display_name)
    """
    first_lower, full_name = _generate_name()
    email = f"{first_lower}@{domain}"
    return email, full_name


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

    # 全局默认值
    default_email_domain = os.environ.get("DEFAULT_EMAIL_DOMAIN", "")
    default_from_name = os.environ.get("DEFAULT_FROM_NAME", "")  # 空则自动生成
    default_ai_prompt = os.environ.get("DEFAULT_AI_PROMPT", "")

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

        # 处理 from_email：账号自定义 > 全局域名自动生成
        from_email = acc.get("from_email", "")
        from_name = acc.get("from_name", "")

        if not from_email and default_email_domain:
            # 自动生成 email 和 name
            from_email, auto_name = _generate_email(default_email_domain)
            if not from_name:
                from_name = auto_name if not default_from_name else default_from_name
        elif not from_name:
            from_name = default_from_name

        # 处理 ai_prompt：账号自定义 > 全局默认
        ai_prompt = acc.get("ai_prompt", "") or default_ai_prompt

        try:
            accounts.append(AccountConfig(
                name=acc.get("name", f"account_{i}"),
                from_email=from_email,
                from_name=from_name,
                to_email=acc.get("to_email", ""),
                cron=acc.get("cron", ""),
                ai_prompt=ai_prompt,
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

