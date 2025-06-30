FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY youtube_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY youtube_service/main.py ./main.py
COPY youtube_service/routers ./routers
COPY youtube_service/services ./services
COPY auth_service ./auth_service

# Copy shared library
COPY shared_lib ./shared_lib

# Environment for Python path
ENV PYTHONPATH=/app

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

