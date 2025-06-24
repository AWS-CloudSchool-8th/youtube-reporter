# app/utils/helpers.py
import re
import time
import hashlib
import json
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs


def extract_youtube_video_id(url: str) -> Optional[str]:
    """YouTube URL에서 video ID 추출"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def validate_youtube_url(url: str) -> bool:
    """YouTube URL 유효성 검증"""
    if not url:
        return False

    # 기본적인 URL 형식 검증
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
    except Exception:
        return False

    # YouTube 도메인 검증
    valid_domains = ['youtube.com', 'www.youtube.com', 'youtu.be', 'www.youtu.be']
    if parsed.netloc not in valid_domains:
        return False

    # Video ID 추출 가능 여부 확인
    video_id = extract_youtube_video_id(url)
    return video_id is not None and len(video_id) == 11


def sanitize_filename(filename: str) -> str:
    """파일명에서 특수문자 제거"""
    # 위험한 문자 제거
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 연속된 공백을 하나로
    filename = re.sub(r'\s+', ' ', filename)
    # 앞뒤 공백 제거
    filename = filename.strip()
    # 길이 제한 (확장자 포함 255자)
    if len(filename) > 250:
        filename = filename[:250]

    return filename


def generate_job_id() -> str:
    """고유한 작업 ID 생성"""
    timestamp = str(int(time.time() * 1000))
    random_part = hashlib.md5(timestamp.encode()).hexdigest()[:8]
    return f"job_{timestamp}_{random_part}"


def format_duration(seconds: float) -> str:
    """초를 읽기 쉬운 형태로 변환"""
    if seconds < 60:
        return f"{seconds:.1f}초"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}분 {remaining_seconds:.1f}초"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}시간 {minutes}분"


def format_file_size(size_bytes: int) -> str:
    """바이트를 읽기 쉬운 크기로 변환"""
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f}{size_names[i]}"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """텍스트를 지정된 길이로 자르기"""
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def clean_text(text: str) -> str:
    """텍스트 정리 (공백, 특수문자 등)"""
    # 연속된 공백을 하나로
    text = re.sub(r'\s+', ' ', text)
    # 앞뒤 공백 제거
    text = text.strip()
    # 특수 유니코드 문자 정리
    text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)

    return text


def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """텍스트에서 키워드 추출 (간단한 방식)"""
    # 한국어 불용어
    stopwords = {
        '은', '는', '이', '가', '을', '를', '의', '에', '에서', '로', '으로',
        '와', '과', '도', '만', '라', '아', '어', '여', '하다', '있다', '없다',
        '그', '저', '이', '그것', '저것', '것', '수', '때', '년', '월', '일',
        '시간', '분', '초', '개', '명', '번', '등', '및', '또는', '그리고'
    }

    # 단어 추출 (2글자 이상)
    words = re.findall(r'\b\w{2,}\b', text.lower())

    # 불용어 제거 및 빈도 계산
    word_freq = {}
    for word in words:
        if word not in stopwords and len(word) >= 2:
            word_freq[word] = word_freq.get(word, 0) + 1

    # 빈도순 정렬
    keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

    return [word for word, freq in keywords[:max_keywords]]


def timing_decorator(func: Callable) -> Callable:
    """함수 실행 시간 측정 데코레이터"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time

        from .logger import log_execution_time
        log_execution_time(func.__name__, execution_time)

        return result

    return wrapper


def retry_with_backoff(
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        exceptions: tuple = (Exception,)
) -> Callable:
    """지수 백오프를 사용한 재시도 데코레이터"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        raise e

                    wait_time = backoff_factor * (2 ** attempt)
                    time.sleep(wait_time)

            return None

        return wrapper

    return decorator


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """안전한 JSON 파싱"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """안전한 JSON 직렬화"""
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return default


def parse_markdown_headers(text: str) -> List[Dict[str, Any]]:
    """마크다운 텍스트에서 헤더 구조 파싱"""
    lines = text.split('\n')
    headers = []

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            title = line.lstrip('#').strip()

            headers.append({
                'level': level,
                'title': title,
                'line_number': i,
                'id': f"header_{len(headers) + 1}"
            })

    return headers


def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """텍스트 읽기 시간 계산 (분)"""
    words = len(text.split())
    reading_time = words / words_per_minute
    return max(1, int(reading_time))


def is_valid_email(email: str) -> bool:
    """이메일 주소 유효성 검증"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """민감한 데이터 마스킹"""
    if len(data) <= visible_chars:
        return mask_char * len(data)

    visible_part = data[:visible_chars]
    masked_part = mask_char * (len(data) - visible_chars)

    return visible_part + masked_part


def generate_cache_key(*args, **kwargs) -> str:
    """캐시 키 생성"""
    key_parts = []

    # 위치 인자 추가
    for arg in args:
        key_parts.append(str(arg))

    # 키워드 인자 추가 (정렬된 순서)
    for key, value in sorted(kwargs.items()):
        key_parts.append(f"{key}={value}")

    # 해시 생성
    key_string = "|".join(key_parts)
    return hashlib.md5(key_string.encode()).hexdigest()


def chunk_text(text: str, max_length: int = 1000, overlap: int = 100) -> List[str]:
    """긴 텍스트를 청크로 분할"""
    if len(text) <= max_length:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_length

        # 단어 경계에서 자르기
        if end < len(text):
            # 마지막 공백 찾기
            space_pos = text.rfind(' ', start, end)
            if space_pos > start:
                end = space_pos

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # 다음 시작점 (오버랩 고려)
        start = max(start + 1, end - overlap)

    return chunks