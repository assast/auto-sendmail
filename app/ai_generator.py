"""
AI 内容生成模块
使用 OpenAI 兼容 API 生成拟人化的日常聊天邮件内容
"""

import logging
from dataclasses import dataclass
from openai import OpenAI

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """你是一个邮件内容生成助手。根据用户设定的角色和场景，生成一封自然、真实的日常聊天邮件。

要求：
1. 内容要像真实的人在写邮件，语气自然亲切，不要有任何 AI 味道
2. 内容适中，不要太长也不要太短（50-200字）
3. 可以聊最近的生活、天气、心情、趣事等日常话题
4. 每次生成的内容都要不同，有随机性和新鲜感
5. 不要使用模板化的开头和结尾

请严格按照以下 JSON 格式返回（不要包含 markdown 代码块标记）：
{"subject": "邮件主题（简短自然，像朋友间发消息）", "body": "邮件正文（纯文本，自然聊天风格）"}"""


@dataclass
class EmailContent:
    """生成的邮件内容"""
    subject: str
    body: str


class AIGenerator:
    """AI 邮件内容生成器"""

    def __init__(self, api_key: str, api_base: str, model: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base,
        )
        self.model = model

    def generate(self, ai_prompt: str, subject_prefix: str = "") -> EmailContent:
        """
        根据给定的 prompt 生成邮件内容

        Args:
            ai_prompt: 用户设定的角色和场景描述
            subject_prefix: 主题前缀

        Returns:
            EmailContent: 包含主题和正文的邮件内容
        """
        logger.info(f"正在使用 {self.model} 生成邮件内容...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE},
                    {"role": "user", "content": ai_prompt},
                ],
                temperature=0.9,
                max_tokens=500,
            )

            raw_content = response.choices[0].message.content.strip()
            logger.debug(f"AI 原始返回: {raw_content}")

            # 解析 JSON 响应
            import json

            # 清理可能的 markdown 代码块标记
            if raw_content.startswith("```"):
                lines = raw_content.split("\n")
                # 移除首尾的 ``` 行
                lines = [l for l in lines if not l.strip().startswith("```")]
                raw_content = "\n".join(lines)

            parsed = json.loads(raw_content)
            subject = parsed.get("subject", "日常问候")
            body = parsed.get("body", "")

            if subject_prefix:
                subject = f"{subject_prefix}{subject}"

            if not body:
                raise ValueError("AI 返回的邮件正文为空")

            logger.info(f"邮件内容生成成功 | 主题: {subject}")
            return EmailContent(subject=subject, body=body)

        except json.JSONDecodeError as e:
            logger.error(f"AI 返回的 JSON 解析失败: {e}\n原始内容: {raw_content}")
            # 降级处理：直接使用原始内容作为正文
            return EmailContent(
                subject=f"{subject_prefix}日常问候" if subject_prefix else "日常问候",
                body=raw_content,
            )
        except Exception as e:
            logger.error(f"AI 内容生成失败: {e}")
            raise
