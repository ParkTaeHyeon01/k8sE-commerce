# 공식 Playwright 이미지는 태그가 파이썬 패키지 버전과 정확히 일치해야 해서 관리가 번거로움
# 대신 일반 파이썬 이미지에 requirements.txt로 설치되는 playwright 버전에 맞는 브라우저를 직접 설치한다
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY . .

# k8s CronJob으로 주기 실행되며, 매 실행마다 trace_id를 새로 생성해 크롤링 -> Kafka 전송까지 수행한다
CMD ["python", "main.py"]
