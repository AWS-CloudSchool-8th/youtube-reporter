FROM python:3.10-slim

WORKDIR /app

# 필수 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY report_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# shared_lib 패키지 설치
COPY shared_lib ./shared_lib
RUN pip install --no-cache-dir -e ./shared_lib

# 서비스 코드 복사
COPY report_service/main.py ./main.py
COPY report_service/routers ./routers
COPY report_service/services ./services

# 종속 서비스 코드 복사
COPY auth_service ./auth_service
COPY analyzer_service ./analyzer_service 

ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

