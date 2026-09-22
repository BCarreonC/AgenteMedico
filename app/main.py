import time
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.config.settings import settings
from app.graph.builder import graph
from app.schemas.request import ChatRequest
from app.utils.logger import (
    compact,
    exception_chain,
    get_logger,
    elapsed_ms,
    pretty_log,
    reset_request_id,
    set_request_id,
)


logger = get_logger("main")


async def check_dependency(
    name: str,
    url: str,
) -> None:
    logger.info(
        "[STARTUP] Comprobando dependencia %s en %s",
        name,
        url,
    )

    try:
        async with httpx.AsyncClient(
            timeout=5.0,
        ) as client:
            response = await client.get(
                url,
            )

        try:
            response_body = response.json()

        except ValueError:
            response_body = response.text

        logger.info(
            "[STARTUP] %s respondió status=%s\n"
            "body=\n%s",
            name,
            response.status_code,
            pretty_log(
                response_body,
                2000,
            ),
        )

    except Exception as exc:
        logger.error(
            "[STARTUP] No fue posible conectar con %s. "
            "Cadena del error: %s",
            name,
            exception_chain(exc),
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("========== INICIANDO MEDICAL AGENT ==========")
    logger.info("NEST_API=%s", settings.NEST_API)
    logger.info("APP_TIMEZONE=%s", settings.APP_TIMEZONE)
    logger.info("OLLAMA_BASE_URL=%s", settings.OLLAMA_BASE_URL)
    logger.info("OLLAMA_MODEL=%s", settings.OLLAMA_MODEL)

    await check_dependency(
        "NestJS",
        f"{settings.NEST_API.rstrip('/')}/health",
    )
    await check_dependency(
        "Ollama",
        f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/tags",
    )

    yield

    logger.info("========== DETENIENDO MEDICAL AGENT ==========")


app = FastAPI(
    title="Medical Agent",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "medical-agent",
    }


@app.post("/chat")
async def chat(
    request: ChatRequest,
) -> dict:
    session_id = (
        request.session_id
        or str(uuid.uuid4())
    )
    request_id = str(uuid.uuid4())
    started_at = time.perf_counter()
    request_id_token = set_request_id(request_id)

    logger.info(
        "[%s] POST /chat session_id=%s message=%r",
        request_id,
        session_id,
        request.message,
    )

    state = {
        "request_id": request_id,
        "message": request.message,
        "history": [],
        "intent": "",
        "confidence": 0.0,
        "entities": {},
        "tool": None,
        "tool_input": {},
        "tool_result": None,
        "response": "",
        "errors": [],
    }

    try:
        graph_started_at = time.perf_counter()

        result = await graph.ainvoke(
            state,
            config={
                "configurable": {
                    "thread_id": session_id,
                },
            },
        )

        graph_elapsed_ms = elapsed_ms(graph_started_at)

        tool_result = result.get(
            "tool_result",
        )

        business_ok = (
            tool_result.get("ok")
            if isinstance(
                tool_result,
                dict,
            )
            else None
        )

        logger.info(
            "[%s] Grafo terminado en %.2f ms. "
            "intent=%s tool=%s confidence=%s errors=%s",
            request_id,
            graph_elapsed_ms,
            result.get("intent"),
            result.get("tool"),
            result.get("confidence"),
            compact(
                result.get(
                    "errors",
                    [],
                ),
                2000,
            ),
        )

        logger.debug(
            "[%s] Estado final:\n%s",
            request_id,
            pretty_log(
                result,
                10000,
            ),
        )

        response_payload = {
            "session_id": session_id,
            "intent": result.get(
                "intent",
                "unknown",
            ),
            "confidence": result.get(
                "confidence",
                0.0,
            ),
            "tool": result.get(
                "tool",
            ),
            "entities": result.get(
                "entities",
                {},
            ),
            "response": result.get(
                "response",
                "",
            ),
            "errors": result.get(
                "errors",
                [],
            ),
        }

        total_elapsed_ms = elapsed_ms(started_at)

        logger.info(
            "[%s] [PERF] request.total elapsed_ms=%.2f "
            "graph_ms=%.2f intent=%s tool=%s "
            "status=completed business_ok=%s",
            request_id,
            total_elapsed_ms,
            graph_elapsed_ms,
            result.get("intent"),
            result.get("tool"),
            business_ok,
        )

        return response_payload

    except Exception as exc:
        total_elapsed_ms = elapsed_ms(started_at)

        logger.error(
            "[%s] [PERF] request.total elapsed_ms=%.2f status=error",
            request_id,
            total_elapsed_ms,
        )

        logger.exception(
            "[%s] Error no controlado ejecutando el grafo. "
            "Cadena=%s",
            request_id,
            exception_chain(exc),
        )

        raise

    finally:
        reset_request_id(request_id_token)
