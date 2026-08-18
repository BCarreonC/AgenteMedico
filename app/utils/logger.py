import json
import logging
import sys
from typing import Any


LOGGER_NAME = "medical_agent"


def _configure_root_logger() -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            logging.Formatter(
                fmt=(
                    "%(asctime)s | %(levelname)-8s | "
                    "%(name)s | %(message)s"
                ),
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)

    return logger


ROOT_LOGGER = _configure_root_logger()


def get_logger(component: str) -> logging.Logger:
    return logging.getLogger(f"{LOGGER_NAME}.{component}")


def pretty(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    except Exception:
        return repr(value)


def compact(value: Any, limit: int = 4000) -> str:
    text = pretty(value)
    if len(text) <= limit:
        return text

    return text[:limit] + "\n... [contenido truncado]"


def exception_chain(exc: BaseException) -> str:
    chain: list[str] = []
    current: BaseException | None = exc
    seen: set[int] = set()

    while current is not None and id(current) not in seen:
        seen.add(id(current))
        chain.append(
            f"{type(current).__name__}: {current!s}"
        )
        current = current.__cause__ or current.__context__

    return " -> ".join(chain)
