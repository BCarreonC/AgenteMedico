import time

from langchain_ollama import ChatOllama

from app.config.settings import settings
from app.utils.logger import (
    elapsed_ms,
    get_logger,
)


logger = get_logger("llm")


planner_llm = ChatOllama(
    model=settings.OLLAMA_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
    
    # Politics for the LLM
    temperature=0,
    reasoning=False,

    # Configuration for the LLM
    num_predict=settings.OLLAMA_NUM_PREDICT,
    keep_alive=settings.OLLAMA_KEEP_ALIVE,

    format="json",
)


async def warmup_llm() -> None:
    """
    Realiza una inferencia pequeña para obligar a Ollama
    a cargar el modelo antes de recibir solicitudes reales.
    """

    started_at = time.perf_counter()

    logger.info(
        "[WARMUP] Preparando modelo %s...",
        settings.OLLAMA_MODEL,
    )

    try:
        response = await planner_llm.ainvoke(
            """
                Devuelve únicamente este JSON:

                {
                "intent": "greeting",
                "confidence": 1.0,
                "entities": {}
                }
            """
        )

        logger.info(
            "[WARMUP] Modelo %s preparado en %.2f ms",
            settings.OLLAMA_MODEL,
            elapsed_ms(started_at),
        )

        logger.debug(
            "[WARMUP] Respuesta=%s",
            response.content,
        )

    except Exception:
        logger.exception(
            "[WARMUP] No fue posible preparar el modelo %s",
            settings.OLLAMA_MODEL,
        )