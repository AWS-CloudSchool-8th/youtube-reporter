# app/test_backend_simple.py
"""백엔드가 정상적으로 실행되는지 테스트"""

import sys
import os
from pathlib import Path

print("🧪 백엔드 단순 테스트 시작")
print("=" * 50)

try:
    # 환경 변수 로드
    from dotenv import load_dotenv

    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
    print(f"✅ .env 파일 로드됨: {env_path}")
except ImportError:
    print("⚠️  python-dotenv가 설치되지 않음")

try:
    # 기본 모듈들 import
    from utils.env_validator import check_environment_comprehensive

    print("✅ env_validator import 성공")

    from utils.logger import setup_logger

    print("✅ logger import 성공")

    from config.settings import api_config, llm_config

    print("✅ config import 성공")

    # 환경 변수 간단 체크
    required = ['VIDCAP_API_KEY', 'OPENAI_API_KEY', 'AWS_REGION', 'S3_BUCKET_NAME']
    missing = []
    for var in required:
        if not os.getenv(var):
            missing.append(var)

    if missing:
        print(f"❌ 누락된 환경 변수: {missing}")
        print("\n💡 .env 파일을 확인하세요:")
        print("VIDCAP_API_KEY=your_key_here")
        print("OPENAI_API_KEY=your_key_here")
        print("AWS_REGION=us-west-2")
        print("S3_BUCKET_NAME=your-bucket-name")
        print("AWS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0")
    else:
        print("✅ 모든 필수 환경 변수 설정됨")

    # 기존 workflow 테스트
    from core.workflow.fsm import run_graph

    print("✅ workflow import 성공")

    print("\n🎉 기본 백엔드 모듈들이 정상 동작합니다!")
    print("이제 API 서버를 실행해보세요:")
    print("cd app/api && python main.py")

except Exception as e:
    print(f"❌ 백엔드 테스트 실패: {e}")
    import traceback

    traceback.print_exc()

    print("\n🔧 문제 해결 방법:")
    print("1. 필요한 패키지 설치: pip install -r requirements.txt")
    print("2. .env 파일 설정 확인")
    print("3. Python 경로 확인")