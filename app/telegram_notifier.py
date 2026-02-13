"""
Telegram 通知模块
发送邮件结果通知到 Telegram
"""

import logging
import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram Bot 通知器"""

    API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = bool(bot_token and chat_id)

        if not self.enabled:
            logger.warning("Telegram 通知未配置 (缺少 TG_BOT_TOKEN 或 TG_CHAT_ID)，将跳过通知")

    def send(self, message: str):
        """发送 Telegram 消息"""
        if not self.enabled:
            return

        url = self.API_URL.format(token=self.bot_token)
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
        }

        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            logger.debug("Telegram 通知发送成功")
        except Exception as e:
            logger.error(f"Telegram 通知发送失败: {e}")

    def notify_success(self, account_name: str, to_email: str, subject: str):
        """通知邮件发送成功"""
        msg = (
            f"✅ <b>邮件发送成功</b>\n"
            f"📋 账号: {account_name}\n"
            f"📮 收件人: {to_email}\n"
            f"📝 主题: {subject}"
        )
        self.send(msg)

    def notify_failure(self, account_name: str, to_email: str, error: str):
        """通知邮件发送失败"""
        msg = (
            f"❌ <b>邮件发送失败</b>\n"
            f"📋 账号: {account_name}\n"
            f"📮 收件人: {to_email}\n"
            f"⚠️ 错误: {error}"
        )
        self.send(msg)
