FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY product.proto .
# proto 정의 → Python 클래스 자동 생성
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. product.proto
COPY run_bench.py .
CMD ["sleep", "infinity"]
