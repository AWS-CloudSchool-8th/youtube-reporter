import tempfile
import uuid
import os
from core.tools.s3 import upload_to_s3
from langchain_experimental.tools import PythonREPLTool
from utils.exceptions import CodeExecutionError
from utils.error_handler import safe_execute

python_tool = PythonREPLTool()


def _generate_visual_from_code_impl(code: str) -> str:
    """실제 시각화 생성 로직 (내부용) - 참고 코드 방식 적용"""
    if not code:
        raise CodeExecutionError("Empty code provided", "generate_visual_from_code")

    print(f"🔍 실행할 코드:\n{code}")  # 디버깅용

    # 코드 실행
    result = python_tool.run(code)
    print(f"🔍 실행 결과: {result}")  # 디버깅용

    # output.png 파일이 생성되었는지 확인
    if os.path.exists("output.png"):
        # 고유 파일명 생성 (참고 코드 방식)
        unique_filename = f"output-{uuid.uuid4().hex[:8]}.png"
        os.rename("output.png", unique_filename)

        # S3에 업로드
        s3_url = upload_to_s3(unique_filename, object_name=unique_filename, content_type="image/png")

        # 로컬 파일 삭제
        os.remove(unique_filename)

        if not s3_url or s3_url.startswith("[Error"):
            raise CodeExecutionError("S3 upload failed", "generate_visual_from_code")

        return s3_url
    else:
        raise CodeExecutionError(f"Image not created: {result}", "generate_visual_from_code")


def generate_visual_from_code(code: str) -> str:
    """안전한 시각화 생성 (에러 처리 포함)"""
    return safe_execute(
        _generate_visual_from_code_impl,
        code,
        context="generate_visual_from_code",
        default_return=""
    )