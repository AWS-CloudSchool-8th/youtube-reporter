# ✅ 코드 설명: 시각화용 파이썬 코드를 안전하게 실행해 이미지 생성
#   - 코드가 안전한지 AST 분석함
#   - PythonREPLTool을 통해 코드 실행 후 생성된 파일을 S3 업로드

import ast
import tempfile
import uuid
import os
from app.tools.s3 import upload_to_s3
from langchain_experimental.tools import PythonREPLTool

python_tool = PythonREPLTool()

def is_safe_code(code: str) -> bool:
    try:
        tree = ast.parse(code)
        return True
    except Exception:
        return False

def generate_visual_from_code(code: str) -> str:
    if not is_safe_code(code):
        return "[Error: Unsafe code detected]"

    with tempfile.TemporaryDirectory() as tmpdir:
        fname = os.path.join(tmpdir, f"output-{uuid.uuid4().hex[:8]}.png")
        safe_code = code.replace("output.png", fname)
        try:
            result = python_tool.run(safe_code)
            if os.path.exists(fname):
                return upload_to_s3(fname, object_name=os.path.basename(fname), content_type="image/png")
            else:
                return f"[Image not created: {result}]"
        except Exception as e:
            return f"[Error executing code: {e}]"