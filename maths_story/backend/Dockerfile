FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Expose backend port
EXPOSE 8001

# Start FastAPI
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]