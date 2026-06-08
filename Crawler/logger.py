# 공통 로깅 설정
# 포맷: [trace_id] 컴포넌트 | 레벨 | 메시지
import logging

_FORMAT = "[%(trace_id)s] %(component)s | %(levelname)s | %(message)s"


def get_logger(component: str, trace_id: str) -> logging.LoggerAdapter:
    """trace_id와 컴포넌트명이 로그 포맷에 자동으로 포함되는 로거를 반환한다."""
    logger = logging.getLogger("crawler")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logging.LoggerAdapter(logger, {"trace_id": trace_id, "component": component})
