FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# requirements 복사 및 설치
COPY document_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 서비스 관련 코드 복사
COPY document_service/main.py ./main.py
COPY document_service/routers ./routers
COPY document_service/services ./services

# shared-lib 복사 (루트 기준 상대 경로로 접근)
# 공유 라이브러리를 /shared_lib로 지정
COPY shared_lib ./shared_lib

# PYTHONPATH 환경 변수 설정
ENV PYTHONPATH="/app"

# FastAPI 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
