FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY product.proto .
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. product.proto
COPY server.py .
CMD ["python", "server.py"]
