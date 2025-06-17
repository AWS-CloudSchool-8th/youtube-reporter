"""YouTube Reporter 메인 실행 파일"""

import sys
from pprint import pprint
from utils.env_validator import check_environment_comprehensive
from utils.logger import setup_logger
from fsm import run_graph

# 로거 설정
logger = setup_logger(__name__)


def main():
    """메인 실행 함수"""
    print("🎬 YouTube Reporter 시작")
    print("=" * 50)

    # 1단계: 환경 변수 검증
    if not check_environment_comprehensive():
        logger.error("환경 변수 검증 실패. 프로그램을 종료합니다.")
        sys.exit(1)

    # 2단계: 사용자 입력 받기
    try:
        print("\n📝 YouTube URL을 입력하세요:")
        url = input("URL: ").strip()

        if not url:
            logger.error("URL이 입력되지 않았습니다.")
            sys.exit(1)

        # 기본적인 YouTube URL 형식 검증
        if not any(domain in url for domain in ["youtube.com", "youtu.be"]):
            logger.warning("입력된 URL이 YouTube URL이 아닐 수 있습니다.")
            confirm = input("계속 진행하시겠습니까? (y/N): ").strip().lower()
            if confirm != 'y':
                print("프로그램을 종료합니다.")
                sys.exit(0)

        logger.info(f"처리할 URL: {url}")

    except KeyboardInterrupt:
        print("\n\n프로그램이 사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"입력 처리 중 오류 발생: {e}")
        sys.exit(1)

    # 3단계: 그래프 실행
    try:
        logger.info("YouTube 영상 처리 시작...")
        result = run_graph(url)

        print("\n" + "=" * 50)
        print("🎉 처리 완료! 결과:")
        print("=" * 50)
        pprint(result)

        # 에러가 포함된 결과인지 확인
        if isinstance(result, dict) and "error" in result:
            logger.warning("결과에 에러가 포함되어 있습니다.")
            return 1

        logger.info("모든 처리가 성공적으로 완료되었습니다.")
        return 0

    except KeyboardInterrupt:
        print("\n\n처리가 사용자에 의해 중단되었습니다.")
        return 0
    except Exception as e:
        logger.error(f"처리 중 예상치 못한 오류 발생: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)