"""
邮件发送模块
使用 Resend API 发送邮件
"""

import logging
import resend

logger = logging.getLogger(__name__)


class EmailSender:
    """Resend 邮件发送器"""

    def __init__(self, api_key: str):
        resend.api_key = api_key

    def send(
        self,
        from_email: str,
        from_name: str,
        to_email: str,
        subject: str,
        body: str,
    ) -> dict:
        """
        发送邮件

        Args:
            from_email: 发件人邮箱
            from_name: 发件人名称
            to_email: 收件人邮箱
            subject: 邮件主题
            body: 邮件正文（纯文本）

        Returns:
            dict: Resend API 返回结果
        """
        sender = f"{from_name} <{from_email}>" if from_name else from_email

        # 将纯文本正文转换为简单 HTML（保留换行等格式）
        html_body = body.replace("\n", "<br>\n")
        html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, 'Segoe UI', sans-serif; font-size: 15px; line-height: 1.8; color: #333; padding: 20px;">
{html_body}
</body>
</html>"""

        params: resend.Emails.SendParams = {
            "from": sender,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        }

        logger.info(f"正在发送邮件: {sender} → {to_email} | 主题: {subject}")

        try:
            result = resend.Emails.send(params)
            logger.info(f"邮件发送成功 ✅ | ID: {result.get('id', 'N/A')}")
            return result
        except Exception as e:
            logger.error(f"邮件发送失败 ❌ | {sender} → {to_email} | 错误: {e}")
            raise
