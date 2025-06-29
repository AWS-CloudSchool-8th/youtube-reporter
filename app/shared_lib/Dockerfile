FROM python:3.10-slim

WORKDIR /app

COPY shared_lib/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY shared_lib ./shared_lib
COPY shared_lib/main.py ./main.py

ENV PYTHONPATH=/app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
