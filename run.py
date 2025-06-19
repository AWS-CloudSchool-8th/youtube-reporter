# run.py (프로젝트 루트)
# !/usr/bin/env python3
"""
YouTube Reporter 실행 파일
"""
import uvicorn
from app.main import create_app


def main():
    """메인 실행 함수"""
    try:
        app = create_app()

        print("🚀 YouTube Reporter 시작")
        print("📖 API 문서: http://localhost:8000/docs")
        print("🌐 프론트엔드: http://localhost:3000")

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )

    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())