import time
from typing import Callable, Any

def handle_throttling(func: Callable, *args, max_retries: int = 3, base_wait: int = 15, **kwargs) -> Any:
    """토큰 제한 오류 처리를 위한 재시도 래퍼"""
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "ThrottlingException" in str(e) and attempt < max_retries - 1:
                wait_time = base_wait * (attempt + 1)
                print(f"⏳ 토큰 제한으로 {wait_time}초 대기 중... (시도 {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                raise e
    
    raise Exception("최대 재시도 횟수 초과")

def truncate_text(text: str, max_length: int = 2000) -> str:
    """텍스트 길이 제한"""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text