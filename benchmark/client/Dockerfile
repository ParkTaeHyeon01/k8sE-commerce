FROM python:3.11-slim
WORKDIR /app
# 시스템 protoc (SHA-NI 불필요, Debian 기본 컴파일)
RUN apt-get update && apt-get install -y protobuf-compiler && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# 빌드 시 grpc_python_plugin 바이너리 추출 (런타임에서 protoc와 함께 사용)
RUN python -c "import grpc_tools, os, shutil; \
    src = os.path.join(os.path.dirname(grpc_tools.__file__), 'grpc_python_plugin'); \
    shutil.copy(src, '/usr/local/bin/grpc_python_plugin')" && \
    chmod +x /usr/local/bin/grpc_python_plugin
COPY product.proto .
COPY run_bench.py .
CMD ["sleep", "infinity"]
