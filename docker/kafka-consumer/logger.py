# 공통 로깅 설정 (Crawler/logger.py와 동일한 포맷을 사용해 추적 ID로 흐름을 이어간다)
# 포맷: [trace_id] 컴포넌트 | 레벨 | 메시지
import logging

_FORMAT = "[%(trace_id)s] %(component)s | %(levelname)s | %(message)s"


def get_logger(component: str, trace_id: str) -> logging.LoggerAdapter:
    """trace_id와 컴포넌트명이 로그 포맷에 자동으로 포함되는 로거를 반환한다.

    크롤러가 메시지에 실어 보낸 trace_id를 그대로 이어받아 사용하므로,
    메시지 하나를 처리할 때마다 그 trace_id로 로거를 새로 만들어 호출한다.
    """
    logger = logging.getLogger("kafka-consumer")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logging.LoggerAdapter(logger, {"trace_id": trace_id, "component": component})
