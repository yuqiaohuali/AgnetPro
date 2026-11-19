import logging
import os
from pathlib import Path

from dotenv import load_dotenv


# 项目根目录，用于定位项目级 .env 文件。
ROOT_DIR = Path(__file__).resolve().parents[2]


def load_config() -> tuple[str, str]:
    """加载钉钉配置并返回 Client ID 与 Client Secret。"""

    load_dotenv(ROOT_DIR / ".env", override=False)

    client_id = os.getenv("DINGDING_ID", "").strip()
    client_secret = os.getenv("DINGDING_SECRET", "").strip()

    if not client_id or not client_secret:
        raise RuntimeError(
            "请在项目根目录 .env 中配置 DINGDING_ID 和 DINGDING_SECRET"
        )

    return client_id, client_secret


def configure_logging() -> None:
    """配置项目统一日志格式，避免业务入口重复配置。"""

    if logging.getLogger().handlers:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
