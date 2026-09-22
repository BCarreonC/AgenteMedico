import json
import logging
import sys
from typing import Any
import time 
from contextvars import ContextVar, Token


LOGGER_NAME = "medical_agent"

REQUEST_ID_CONTEXT: ContextVar[str] = ContextVar(
    "medical_agent_request_id",
    default="sin-request-id",
)

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

def set_request_id(request_id: str) -> Token:
    """Asocia el request_id al contexto async actual."""
    return REQUEST_ID_CONTEXT.set(request_id)


def reset_request_id(token: Token) -> None:
    """Restaura el contexto previo del request_id."""
    REQUEST_ID_CONTEXT.reset(token)


def get_request_id() -> str:
    """Obtiene el request_id del contexto async actual."""
    return REQUEST_ID_CONTEXT.get()


def elapsed_ms(started_at: float) -> float:
    """Convierte un intervalo de perf_counter a milisegundos."""
    return (time.perf_counter() - started_at) * 1000


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


def compact(
    value: Any,
    limit: int = 4000,
) -> str:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

    except Exception:
        text = repr(value)

    if len(text) <= limit:
        return text

    return (
        text[:limit]
        + "... [contenido truncado]"
    )

def log_text(
    value: Any,
    limit: int = 4000,
) -> str:
    if value is None:
        return ""

    text = str(value)

    if len(text) <= limit:
        return text

    return (
        text[:limit]
        + "\n... [contenido truncado]"
    )

def pretty_log(
    value: Any,
    limit: int = 10000,
) -> str:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

    except Exception:
        text = str(value)

    if len(text) <= limit:
        return text

    return (
        text[:limit]
        + "\n... [contenido truncado]"
    )

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
