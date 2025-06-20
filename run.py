#!/usr/bin/env python3
"""
YouTube 보고서 생성기 실행 스크립트
"""

import uvicorn
import os
import sys

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("YouTube 보고서 생성기를 시작합니다...")
    print("브라우저에서 http://localhost:8000 으로 접속하세요")
    print("종료하려면 Ctrl+C를 누르세요")
    print("-" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )