import logging

_FORMAT = "[%(trace_id)s] %(component)s | %(levelname)s | %(message)s"


def get_logger(component: str, trace_id: str = "-") -> logging.LoggerAdapter:
    logger = logging.getLogger("product")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logging.LoggerAdapter(logger, {"trace_id": trace_id, "component": component})
