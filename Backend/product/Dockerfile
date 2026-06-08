# product 서비스: Kafka Consumer가 상품 메시지를 받아 MongoDB에 저장한다 (브라우저 불필요)
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# k8s에서는 Deployment로 상시 실행되며, 메시지 수신 시마다 trace_id로 로그를 남긴다
CMD ["python", "consumer.py"]
