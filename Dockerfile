FROM python:3.11-slim

WORKDIR /app

# Install only the backend's actual dependencies (6 packages)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full repo (backend code + analytics parquet files)
COPY . .

# Run from the backend directory so `main:app` resolves correctly
WORKDIR /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
