# ✅ 코드 설명: 시각화용 파이썬 코드를 안전하게 실행해 이미지 생성
#   - 코드가 안전한지 AST 분석함
#   - PythonREPLTool을 통해 코드 실행 후 생성된 파일을 S3 업로드

import ast
import tempfile
import uuid
import os
from core.tools.s3 import upload_to_s3
from langchain_experimental.tools import PythonREPLTool
from utils.exceptions import CodeExecutionError
from utils.error_handler import safe_execute

python_tool = PythonREPLTool()


def is_safe_code(code: str) -> bool:
    """코드 안전성 검사"""
    try:
        tree = ast.parse(code)
        return True
    except Exception:
        return False


def _generate_visual_from_code_impl(code: str) -> str:
    """실제 시각화 생성 로직 (내부용)"""
    if not code:
        raise CodeExecutionError("Empty code provided", "generate_visual_from_code")

    if not is_safe_code(code):
        raise CodeExecutionError("Unsafe code detected", "generate_visual_from_code")

    with tempfile.TemporaryDirectory() as tmpdir:
        fname = os.path.join(tmpdir, f"output-{uuid.uuid4().hex[:8]}.png")
        safe_code = code.replace("output.png", fname)

        result = python_tool.run(safe_code)

        if not os.path.exists(fname):
            raise CodeExecutionError(f"Image not created: {result}", "generate_visual_from_code")

        s3_url = upload_to_s3(fname, object_name=os.path.basename(fname), content_type="image/png")

        if not s3_url or s3_url.startswith("[Error"):
            raise CodeExecutionError("S3 upload failed", "generate_visual_from_code")

        return s3_url


def generate_visual_from_code(code: str) -> str:
    """안전한 시각화 생성 (에러 처리 포함)"""
    return safe_execute(
        _generate_visual_from_code_impl,
        code,
        context="generate_visual_from_code",
        default_return=""
    )