# app/utils/logger.py
import logging
import sys
from typing import Optional
from ..core.config import settings


class ColoredFormatter(logging.Formatter):
    """컬러 로깅을 위한 커스텀 포매터"""

    # ANSI 색상 코드
    COLORS = {
        'DEBUG': '\033[36m',  # 청록색
        'INFO': '\033[32m',  # 녹색
        'WARNING': '\033[33m',  # 노란색
        'ERROR': '\033[31m',  # 빨간색
        'CRITICAL': '\033[35m',  # 자홍색
        'RESET': '\033[0m'  # 리셋
    }

    def format(self, record):
        # 로그 레벨에 따른 색상 적용
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset_color = self.COLORS['RESET']

        # 레코드 레벨명에 색상 적용
        record.levelname = f"{log_color}{record.levelname}{reset_color}"

        return super().format(record)


def get_logger(name: str) -> logging.Logger:
    """로거 생성 및 설정"""
    logger = logging.getLogger(name)

    # 이미 설정된 로거는 반환
    if logger.handlers:
        return logger

    # 로그 레벨 설정
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # 콘솔 핸들러 생성
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # 포매터 설정
    if sys.stdout.isatty():  # 터미널에서 실행 중인 경우 컬러 적용
        formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:  # 파일 출력이나 로그 수집 시스템의 경우 컬러 없이
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 상위 로거로 전파 방지
    logger.propagate = False

    return logger


def setup_root_logger():
    """루트 로거 설정"""
    root_logger = logging.getLogger()

    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 새 핸들러 추가
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))


def log_function_call(func_name: str, *args, **kwargs):
    """함수 호출 로깅 데코레이터용 헬퍼"""
    logger = get_logger("function_calls")
    args_str = ', '.join([str(arg) for arg in args])
    kwargs_str = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
    params = ', '.join(filter(None, [args_str, kwargs_str]))
    logger.debug(f"🔧 {func_name}({params}) 호출")


def log_execution_time(func_name: str, execution_time: float):
    """실행 시간 로깅"""
    logger = get_logger("performance")
    if execution_time > 10:
        logger.warning(f"⏱️ {func_name} 실행 시간: {execution_time:.2f}초 (느림)")
    elif execution_time > 5:
        logger.info(f"⏱️ {func_name} 실행 시간: {execution_time:.2f}초")
    else:
        logger.debug(f"⏱️ {func_name} 실행 시간: {execution_time:.2f}초")


# 초기 설정
if settings.debug:
    # 디버그 모드에서는 더 자세한 로깅
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.DEBUG)
else:
    # 프로덕션 모드에서는 핵심 로그만
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# 외부 라이브러리 로깅 레벨 조정
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# LangChain 관련 로깅
if not settings.debug:
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("langchain_core").setLevel(logging.WARNING)
    logging.getLogger("langchain_aws").setLevel(logging.WARNING)
    logging.getLogger("langgraph").setLevel(logging.WARNING)