"""
定时调度模块
使用 APScheduler 为每个账号创建独立的 cron 定时任务
"""

import logging
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import AppConfig, AccountConfig
from app.ai_generator import AIGenerator
from app.email_sender import EmailSender
from app.telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)


def send_email_task(
    account: AccountConfig,
    ai_generator: AIGenerator,
    email_sender: EmailSender,
    tg_notifier: TelegramNotifier,
):
    """
    单个账号的邮件发送任务
    流程：AI 生成内容 → 发送邮件 → TG 通知 → 记录日志
    """
    logger.info(f"{'='*50}")
    logger.info(f"⏰ 触发定时任务: [{account.name}]")
    logger.info(f"   时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Step 1: AI 生成邮件内容
        content = ai_generator.generate(
            ai_prompt=account.ai_prompt,
            subject_prefix=account.subject_prefix,
        )

        # Step 2: 发送邮件
        email_sender.send(
            from_email=account.from_email,
            from_name=account.from_name,
            to_email=account.to_email,
            subject=content.subject,
            body=content.body,
        )

        logger.info(f"✅ [{account.name}] 任务完成")

        # Step 3: TG 通知成功
        tg_notifier.notify_success(
            account_name=account.name,
            to_email=account.to_email,
            subject=content.subject,
        )

    except Exception as e:
        logger.error(f"❌ [{account.name}] 任务失败: {e}", exc_info=True)

        # TG 通知失败
        tg_notifier.notify_failure(
            account_name=account.name,
            to_email=account.to_email,
            error=str(e),
        )

    logger.info(f"{'='*50}")


def parse_cron(cron_expr: str) -> CronTrigger:
    """
    解析 5 位 cron 表达式为 APScheduler CronTrigger

    格式：分 时 日 月 周
    示例：30 8 * * * → 每天 8:30
          0 */2 * * * → 每 2 小时
    """
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        raise ValueError(f"cron 表达式需要 5 个字段，当前: '{cron_expr}'")

    minute, hour, day, month, day_of_week = parts
    return CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
    )


def create_scheduler(config: AppConfig) -> BlockingScheduler:
    """
    根据配置创建调度器，为每个账号注册独立的 cron 任务

    Args:
        config: 应用配置

    Returns:
        BlockingScheduler: 配置好的调度器实例
    """
    scheduler = BlockingScheduler(timezone=config.timezone)

    # 初始化共享组件
    ai_generator = AIGenerator(
        api_key=config.ai_api_key,
        api_base=config.ai_api_base,
        model=config.ai_model,
    )
    email_sender = EmailSender(api_key=config.resend_api_key)
    tg_notifier = TelegramNotifier(
        bot_token=config.tg_bot_token,
        chat_id=config.tg_chat_id,
    )

    # 为每个账号注册定时任务
    for account in config.accounts:
        try:
            trigger = parse_cron(account.cron)
            scheduler.add_job(
                send_email_task,
                trigger=trigger,
                args=[account, ai_generator, email_sender, tg_notifier],
                id=f"sendmail_{account.name}",
                name=f"发送邮件 [{account.name}]",
                misfire_grace_time=300,  # 5 分钟容错
            )
            logger.info(
                f"📅 已注册定时任务: [{account.name}] "
                f"cron={account.cron} | {account.from_name}<{account.from_email}> → {account.to_email}"
            )
        except Exception as e:
            logger.error(f"❌ 注册任务失败 [{account.name}]: {e}")
            raise

    return scheduler
