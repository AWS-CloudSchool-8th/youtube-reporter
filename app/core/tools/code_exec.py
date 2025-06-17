import tempfile
import uuid
import os
import matplotlib
# GUI 백엔드 비활성화
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from core.tools.s3 import upload_to_s3
from langchain_experimental.tools import PythonREPLTool
from utils.exceptions import CodeExecutionError
from utils.error_handler import safe_execute

# 한글 폰트 설정
plt.rcParams['font.family'] = ['DejaVu Sans', 'Malgun Gothic', 'AppleGothic', 'Nanum Gothic']
plt.rcParams['axes.unicode_minus'] = False

python_tool = PythonREPLTool()


def _generate_visual_from_code_impl(code: str) -> str:
    """실제 시각화 생성 로직 (내부용) - 개선된 버전"""
    if not code:
        raise CodeExecutionError("Empty code provided", "generate_visual_from_code")

    print(f"🔍 실행할 코드:\n{code}")

    # 한글 폰트 설정을 코드에 추가
    font_setup = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정
plt.rcParams['font.family'] = ['DejaVu Sans', 'Malgun Gothic', 'AppleGothic', 'Nanum Gothic']
plt.rcParams['axes.unicode_minus'] = False

# 사용 가능한 한글 폰트 찾기
available_fonts = [f.name for f in fm.fontManager.ttflist]
korean_fonts = [font for font in available_fonts if any(k in font for k in ['Nanum', 'Malgun', 'Apple', 'Batang', 'Dotum'])]
if korean_fonts:
    plt.rcParams['font.family'] = korean_fonts[0]
"""

    # 폰트 설정을 원본 코드에 추가
    enhanced_code = font_setup + "\n" + code

    try:
        # 코드 실행
        result = python_tool.run(enhanced_code)
        print(f"🔍 실행 결과: {result}")

        # output.png 파일이 생성되었는지 확인
        if os.path.exists("output.png"):
            # 고유 파일명 생성
            unique_filename = f"output-{uuid.uuid4().hex[:8]}.png"
            os.rename("output.png", unique_filename)

            # S3에 업로드 (업로드 실패 시 로컬 파일 URL 반환)
            s3_url = upload_to_s3(unique_filename, object_name=unique_filename, content_type="image/png")

            # 로컬 파일 삭제
            if os.path.exists(unique_filename):
                os.remove(unique_filename)

            if s3_url and not s3_url.startswith("[Error"):
                return s3_url
            else:
                # S3 업로드 실패 시 대체 방안
                print(f"⚠️ S3 업로드 실패: {s3_url}")
                return f"[Chart generated but upload failed: {s3_url}]"
        else:
            raise CodeExecutionError(f"Image not created: {result}", "generate_visual_from_code")

    except Exception as e:
        print(f"❌ 코드 실행 중 오류: {e}")
        raise CodeExecutionError(f"Code execution failed: {str(e)}", "generate_visual_from_code")


def generate_visual_from_code(code: str) -> str:
    """안전한 시각화 생성 (에러 처리 포함)"""
    return safe_execute(
        _generate_visual_from_code_impl,
        code,
        context="generate_visual_from_code",
        default_return=""
    )