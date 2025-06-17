"""로깅 시스템 설정"""

import logging
import sys
import os
from typing import Optional


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    프로젝트 전용 로거 설정

    Args:
        name: 로거 이름 (보통 __name__ 사용)
        level: 로그 레벨 (환경 변수에서 자동 가져옴)

    Returns:
        설정된 로거 인스턴스
    """
    # 환경 변수에서 로그 레벨 가져오기
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()

    logger = logging.getLogger(name)

    # 이미 핸들러가 설정되어 있으면 중복 설정 방지
    if logger.handlers:
        return logger

    # 핸들러 생성
    handler = logging.StreamHandler(sys.stdout)

    # 포맷터 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)

    # 로거에 핸들러 추가
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, level, logging.INFO))

    # 부모 로거로의 전파 방지 (중복 로그 방지)
    logger.propagate = False

    return logger


def get_project_logger(module_name: str = None) -> logging.Logger:
    """
    프로젝트 전용 로거 가져오기 (간편 함수)

    Args:
        module_name: 모듈 이름 (기본값: 'youtube_reporter')

    Returns:
        로거 인스턴스
    """
    if module_name is None:
        module_name = "youtube_reporter"

    return setup_logger(module_name)