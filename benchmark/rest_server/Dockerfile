FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN CC=false pip install --no-cache-dir --no-binary pymongo -r requirements.txt
COPY main.py .
CMD ["python", "main.py"]
