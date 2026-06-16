FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN CC=false pip install --no-cache-dir --no-binary pymongo -r requirements.txt
COPY product.proto .
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. product.proto
COPY server.py .
CMD ["python", "server.py"]
