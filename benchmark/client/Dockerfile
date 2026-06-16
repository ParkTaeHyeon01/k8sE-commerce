FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# proto 파일과 벤치마크 스크립트 복사 (_pb2.py는 시연 시 직접 생성)
COPY product.proto .
COPY run_bench.py .
CMD ["sleep", "infinity"]
