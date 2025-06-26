FROM python:3.10-slim

WORKDIR /app

# shared_lib, report_service 포함 복사
COPY app/shared_lib /app/shared_lib
COPY app/report_service /app/report_service
ENV PYTHONPATH="/app"

# shared_lib 설치
RUN pip install /app/shared_lib

# requirements 설치
COPY app/analyzer_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# analyzer_service 복사
COPY app/analyzer_service /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
