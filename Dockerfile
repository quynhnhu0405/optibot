FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source and project folders.
COPY app/ app/
COPY data/ data/
COPY markdown/ markdown/

# Run the sync once and exit.
CMD ["python", "app/main.py"]
