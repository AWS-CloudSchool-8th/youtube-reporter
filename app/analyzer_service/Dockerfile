FROM python:3.10-slim

WORKDIR /app

# requirements
COPY analyzer_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app code
COPY analyzer_service/main.py ./main.py
COPY analyzer_service/routers ./routers
COPY analyzer_service/services ./services
COPY report_service ./report_service


# shared_lib, auth_service 등 통신/의존 필요한 경우만 포함
COPY shared_lib ./shared_lib
COPY auth_service ./auth_service

ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
