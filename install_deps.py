#!/usr/bin/env python3
"""
필요한 패키지 설치 스크립트
사용법: python install_deps.py
"""

import subprocess
import sys

def install_package(package):
    """패키지 설치"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} 설치 완료")
    except subprocess.CalledProcessError:
        print(f"❌ {package} 설치 실패")

def main():
    print("🔧 requirements.txt에서 패키지들을 설치합니다...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 모든 패키지 설치 완료!")
    except subprocess.CalledProcessError as e:
        print(f"❌ 패키지 설치 실패: {e}")
        print("하나씩 수동 설치를 시도합니다...")
        
        # 필수 패키지들만 수동 설치
        essential_packages = [
            "fastapi",
            "uvicorn",
            "python-jose[cryptography]",
            "requests",
            "python-dotenv",
            "boto3"
        ]
        
        for package in essential_packages:
            install_package(package)
    
    print("\n✅ 설치 완료!")
    print("이제 python run_server.py로 서버를 실행하세요.")

if __name__ == "__main__":
    main()