FROM python:3.10-slim

WORKDIR /app

# 현재 컨텍스트에 있는 파일 복사
COPY auth_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY auth_service/main.py ./main.py
COPY auth_service/routers ./routers
COPY auth_service/services ./services

# shared_lib 복사 (컨텍스트 밖이라 불가능 ?> 해결책 아래 참고)
# COPY ../shared_lib /shared_lib  ? 이렇게 쓰면 안 됨

# 임시 해결: shared_lib을 이 디렉토리로 **심볼릭 링크 또는 복사**
# 또는 아래 방법으로 해결 ↓↓↓

# FastAPI 앱 코드 복사
COPY . .

# PYTHONPATH 설정
ENV PYTHONPATH="/app:/shared_lib"

# FastAPI 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
