"""통일된 에러 처리 유틸리티"""

from typing import Any, Dict, Optional
from utils.exceptions import YouTubeReporterError
from utils.logger import setup_logger

# 모듈별 로거 생성
logger = setup_logger(__name__)

def handle_error(
    e: Exception,
    context: str,
    default_return: Any = None,
    log_level: str = "error"
) -> Any:
    """
    통일된 에러 처리 함수

    Args:
        e: 발생한 예외
        context: 에러 발생 컨텍스트 (함수명, 작업 설명 등)
        default_return: 기본 반환값 (dict, str 등)
        log_level: 로그 레벨 ("error", "warning", "info")

    Returns:
        에러 정보가 포함된 기본 반환값
    """
    error_msg = str(e)

    # 로깅
    if log_level == "error":
        logger.error(f"Error in {context}: {error_msg}", exc_info=True)
    elif log_level == "warning":
        logger.warning(f"Warning in {context}: {error_msg}")
    else:
        logger.info(f"Info in {context}: {error_msg}")

    # 반환값 생성
    if isinstance(default_return, dict):
        return {**default_return, "error": error_msg, "context": context}
    elif isinstance(default_return, str):
        return f"[Error in {context}: {error_msg}]"
    else:
        return f"[Error in {context}: {error_msg}]"

def safe_execute(func, *args, context: str = None, default_return: Any = None, **kwargs):
    """
    안전한 함수 실행 래퍼

    Args:
        func: 실행할 함수
        *args: 함수 인자
        context: 에러 컨텍스트 (기본값: 함수명)
        default_return: 에러 시 반환값
        **kwargs: 함수 키워드 인자

    Returns:
        함수 실행 결과 또는 에러 정보
    """
    context = context or func.__name__
    try:
        logger.debug(f"Executing {context}")
        result = func(*args, **kwargs)
        logger.debug(f"Successfully completed {context}")
        return result
    except YouTubeReporterError as e:
        return handle_error(e, context, default_return)
    except Exception as e:
        return handle_error(e, context, default_return)