"""
Auto-Sendmail 入口
使用 AI 生成拟人化邮件内容，通过 Resend API 定时发送
"""

import logging
import sys

from dotenv import load_dotenv

from app.config import load_config
from app.scheduler import create_scheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🚀 Auto-Sendmail 启动中...")
    logger.info("=" * 60)

    # 加载 .env 文件（Docker 环境中可能不存在，不报错）
    load_dotenv(override=False)

    try:
        # 加载配置
        config = load_config()

        # 创建并启动调度器
        scheduler = create_scheduler(config)

        logger.info("")
        logger.info("✅ 所有定时任务已注册，调度器运行中...")
        logger.info("   按 Ctrl+C 停止")
        logger.info("")

        scheduler.start()

    except KeyboardInterrupt:
        logger.info("👋 收到停止信号，正在关闭...")
    except Exception as e:
        logger.error(f"💥 启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
