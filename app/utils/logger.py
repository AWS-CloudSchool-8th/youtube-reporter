

# app/utils/logger.py
import logging
import sys
from .config import Config


def get_logger(name: str) -> logging.Logger:
    """로거 생성"""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    # 핸들러 설정
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
    logger.propagate = False

    return logger


