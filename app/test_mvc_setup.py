# test_mvc_setup.py
# app 폴더에서 실행하세요

import sys
import os
from pathlib import Path


def test_mvc_imports():
    """MVC 모듈들이 제대로 import되는지 테스트"""
    print("🧪 MVC 구조 테스트 시작")
    print("=" * 50)

    try:
        # 환경 변수 로드
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 환경 변수 로드 성공")

        # 모델 테스트
        from models.report import Report, ReportSection, VisualizationType
        print("✅ Models import 성공")

        # 서비스 테스트
        from services.youtube_service import YouTubeService
        from services.claude_service import ClaudeService
        print("✅ Services import 성공")

        # 컨트롤러 테스트
        from controllers.report_controller import ReportController
        print("✅ Controllers import 성공")

        # 스키마 테스트
        from views.schemas import ProcessVideoRequest, ReportResponse
        print("✅ Views/Schemas import 성공")

        # 실제 객체 생성 테스트
        controller = ReportController()
        print("✅ ReportController 생성 성공")

        # 기본 데이터 모델 테스트
        report = Report(title="테스트", youtube_url="https://youtube.com/test")
        print(f"✅ Report 모델 생성 성공 (ID: {report.id})")

        print("\n🎉 모든 MVC 구조 테스트 통과!")
        return True

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_mvc_imports()
    if success:
        print("\n✅ MVC 구조가 올바르게 설정되었습니다!")
        print("🚀 이제 API 서버를 시작할 수 있습니다:")
        print("   cd app/api && python main.py")
    else:
        print("\n❌ MVC 구조 설정에 문제가 있습니다.")
        sys.exit(1)