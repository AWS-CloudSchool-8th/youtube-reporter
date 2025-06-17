"""환경 변수 검증 유틸리티"""

import os
import sys
from typing import List, Optional, Dict
from dataclasses import dataclass


@dataclass
class EnvVar:
    """환경 변수 정의"""
    name: str
    description: str
    required: bool = True
    default: str = None


# 필수 환경 변수 정의
REQUIRED_ENV_VARS = [
    EnvVar("VIDCAP_API_KEY", "VidCap API 키 (YouTube 자막 추출용)", required=True),
    EnvVar("OPENAI_API_KEY", "OpenAI API 키 (DALL-E 이미지 생성용)", required=True),
    EnvVar("AWS_REGION", "AWS 리전 (예: us-west-2)", required=True),
    EnvVar("S3_BUCKET_NAME", "S3 버킷 이름 (이미지 저장용)", required=True),
    EnvVar("AWS_BEDROCK_MODEL_ID", "AWS Bedrock 모델 ID", required=True),
]

# 선택적 환경 변수 정의
OPTIONAL_ENV_VARS = [
    EnvVar("LOG_LEVEL", "로그 레벨 (DEBUG, INFO, WARNING, ERROR)", required=False, default="INFO"),
    EnvVar("PYTHONPATH", "Python 경로", required=False),
    EnvVar("VIDCAP_API_URL", "VidCap API URL", required=False, default="https://vidcap.xyz/api/v1/youtube/caption"),
    EnvVar("DALLE_MODEL", "DALL-E 모델명", required=False, default="dall-e-3"),
    EnvVar("DALLE_IMAGE_SIZE", "DALL-E 이미지 크기", required=False, default="1024x1024"),
    EnvVar("LLM_TEMPERATURE", "LLM 온도 설정", required=False, default="0.7"),
    EnvVar("LLM_MAX_TOKENS", "LLM 최대 토큰 수", required=False, default="4096"),
    # LangChain 추적 설정
    EnvVar("LANGCHAIN_API_KEY", "LangChain API 키 (LangSmith 추적용)", required=False),
    EnvVar("LANGCHAIN_ENDPOINT", "LangChain 엔드포인트", required=False, default="https://api.smith.langchain.com"),
    EnvVar("LANGCHAIN_PROJECT", "LangChain 프로젝트명", required=False, default="youtube-reporter"),
    EnvVar("LANGCHAIN_TRACING_V2", "LangChain 추적 활성화", required=False, default="true"),
]


def validate_environment() -> Optional[List[str]]:
    """
    필수 환경 변수 검증

    Returns:
        None: 모든 환경 변수가 설정됨
        List[str]: 누락된 환경 변수 목록
    """
    missing_vars = []

    print("🔍 환경 변수 검증 중...")
    print("-" * 50)

    # 필수 환경 변수 검사
    for env_var in REQUIRED_ENV_VARS:
        value = os.getenv(env_var.name)
        if not value:
            missing_vars.append(env_var.name)
            print(f"❌ {env_var.name}: 누락됨 - {env_var.description}")
        else:
            # 민감한 정보는 마스킹하여 표시
            if "KEY" in env_var.name or "SECRET" in env_var.name:
                masked_value = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "*" * len(value)
                print(f"✅ {env_var.name}: {masked_value}")
            else:
                print(f"✅ {env_var.name}: {value}")

    print("-" * 50)

    # 선택적 환경 변수 검사 및 기본값 설정
    for env_var in OPTIONAL_ENV_VARS:
        value = os.getenv(env_var.name)
        if not value and env_var.default:
            os.environ[env_var.name] = env_var.default
            print(f"🔧 {env_var.name}: 기본값 설정됨 ({env_var.default})")
        elif value:
            print(f"✅ {env_var.name}: {value}")
        else:
            print(f"ℹ️  {env_var.name}: 설정되지 않음 (선택사항)")

    if missing_vars:
        print("\n❌ 환경 변수 검증 실패!")
        print(f"누락된 변수: {', '.join(missing_vars)}")
        print("\n📝 해결 방법:")
        print("1. .env 파일을 생성하고 다음 변수들을 설정하세요:")
        for var_name in missing_vars:
            env_var = next(v for v in REQUIRED_ENV_VARS if v.name == var_name)
            print(f"   {var_name}=your_value_here  # {env_var.description}")
        print("\n2. 또는 시스템 환경 변수로 설정하세요")
        return missing_vars
    else:
        print("✅ 모든 필수 환경 변수가 설정되었습니다!")
        return None


def validate_environment_values() -> Dict[str, List[str]]:
    """
    환경 변수 값의 유효성 검증

    Returns:
        Dict[str, List[str]]: 변수별 검증 오류 목록
    """
    errors = {}

    print("\n🔍 환경 변수 값 검증 중...")
    print("-" * 50)

    # AWS 리전 검증
    aws_region = os.getenv("AWS_REGION")
    if aws_region:
        import re
        if not re.match(r'^[a-z]{2}-[a-z]+-\d+$', aws_region):
            errors.setdefault("AWS_REGION", []).append(f"잘못된 리전 형식: {aws_region}")
            print(f"⚠️  AWS_REGION: 형식이 올바르지 않을 수 있습니다 ({aws_region})")
        else:
            print(f"✅ AWS_REGION: 형식이 올바릅니다 ({aws_region})")

    # S3 버킷 이름 검증
    s3_bucket = os.getenv("S3_BUCKET_NAME")
    if s3_bucket:
        import re
        if not re.match(r'^[a-z0-9][a-z0-9.-]*[a-z0-9]$', s3_bucket) or len(s3_bucket) < 3 or len(s3_bucket) > 63:
            errors.setdefault("S3_BUCKET_NAME", []).append(f"잘못된 S3 버킷 이름: {s3_bucket}")
            print(f"⚠️  S3_BUCKET_NAME: 명명 규칙에 맞지 않을 수 있습니다 ({s3_bucket})")
        else:
            print(f"✅ S3_BUCKET_NAME: 형식이 올바릅니다 ({s3_bucket})")

    # Bedrock 모델 ID 검증
    model_id = os.getenv("AWS_BEDROCK_MODEL_ID")
    if model_id:
        if not model_id.startswith(("anthropic.", "amazon.", "ai21.", "cohere.", "meta.")):
            errors.setdefault("AWS_BEDROCK_MODEL_ID", []).append(f"알 수 없는 모델 제공업체: {model_id}")
            print(f"⚠️  AWS_BEDROCK_MODEL_ID: 지원되지 않는 모델일 수 있습니다 ({model_id})")
        else:
            print(f"✅ AWS_BEDROCK_MODEL_ID: 올바른 형식입니다 ({model_id})")

    # API 키 길이 검증
    api_keys = ["VIDCAP_API_KEY", "OPENAI_API_KEY"]
    for key_name in api_keys:
        key_value = os.getenv(key_name)
        if key_value:
            if len(key_value) < 10:
                errors.setdefault(key_name, []).append("API 키가 너무 짧습니다")
                print(f"⚠️  {key_name}: 길이가 너무 짧을 수 있습니다")
            else:
                print(f"✅ {key_name}: 길이가 적절합니다")

    # 숫자 값 검증
    numeric_vars = {
        "LLM_TEMPERATURE": (0.0, 2.0),
        "LLM_MAX_TOKENS": (100, 100000)
    }

    for var_name, (min_val, max_val) in numeric_vars.items():
        value = os.getenv(var_name)
        if value:
            try:
                numeric_value = float(value)
                if not (min_val <= numeric_value <= max_val):
                    errors.setdefault(var_name, []).append(f"값이 범위를 벗어남: {value} (범위: {min_val}-{max_val})")
                    print(f"⚠️  {var_name}: 값이 권장 범위를 벗어납니다 ({value})")
                else:
                    print(f"✅ {var_name}: 값이 적절합니다 ({value})")
            except ValueError:
                errors.setdefault(var_name, []).append(f"숫자가 아님: {value}")
                print(f"⚠️  {var_name}: 숫자 형식이 아닙니다 ({value})")

    if errors:
        print(f"\n⚠️  {len(errors)}개의 값 검증 경고가 있습니다.")
        for var_name, error_list in errors.items():
            for error in error_list:
                print(f"   {var_name}: {error}")
    else:
        print("✅ 모든 환경 변수 값이 올바른 형식입니다!")

    return errors


def check_environment_comprehensive() -> bool:
    """
    종합적인 환경 변수 검증

    Returns:
        bool: 모든 검증 통과 여부
    """
    print("🚀 YouTube Reporter 환경 검증 시작")
    print("=" * 60)

    # 1단계: 필수 환경 변수 존재 여부 검증
    missing_vars = validate_environment()

    if missing_vars:
        print("\n💡 .env 파일 예시:")
        print("-" * 30)
        print("# YouTube Reporter 설정")
        for env_var in REQUIRED_ENV_VARS:
            if env_var.name in missing_vars:
                print(f"{env_var.name}=your_key_here")
        print("\n# 선택적 설정 (기본값 있음)")
        for env_var in OPTIONAL_ENV_VARS:
            if env_var.default:
                print(f"# {env_var.name}={env_var.default}")
        print("-" * 30)
        return False

    # 2단계: 환경 변수 값 유효성 검증
    value_errors = validate_environment_values()

    if value_errors:
        print("\n⚠️  일부 환경 변수 값에 문제가 있을 수 있지만 실행은 계속됩니다.")
        return True  # 경고는 있지만 실행 가능

    print("\n🎉 모든 환경 검증이 완료되었습니다!")
    print("=" * 60)
    return True