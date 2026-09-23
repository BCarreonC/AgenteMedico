import time
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any


from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import ChatOllama

from app.config.settings import settings
from app.graph.state import AgentState
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.utils.logger import (
    compact,
    exception_chain,
    get_logger,
    elapsed_ms,
    log_text,
    pretty_log,
)

logger = get_logger("planner")

llm = ChatOllama(
    model=settings.OLLAMA_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
    temperature=0,
    format="json",

    reasoning=False,
    num_predict=settings.OLLAMA_NUM_PREDICT,
    keep_alive=settings.OLLAMA_KEEP_ALIVE,
)

parser = JsonOutputParser()

ALLOWED_INTENTS = {
    "search_patient",
    "check_appointment_availability",
    "schedule_appointment",
    "list_appointments",
    "cancel_appointment",
    "reschedule_appointment",
    "confirm_appointment",
    "complete_appointment",
    "mark_appointment_no_show",
    "search_document",
    "greeting",
    "unknown",
}

INTENT_ALIASES = {
    "saludo": "greeting",
    "hello": "greeting",
    "buscar_paciente": "search_patient",
    "consultar_disponibilidad": "check_appointment_availability",
    "check_availability": "check_appointment_availability",
    "appointment_availability": "check_appointment_availability",
    "agendar_cita": "schedule_appointment",
    "crear_cita": "schedule_appointment",
    "create_appointment": "schedule_appointment",
    "consultar_citas": "list_appointments",
    "listar_citas": "list_appointments",
    "cancelar_cita": "cancel_appointment",
    "reprogramar_cita": "reschedule_appointment",
    "confirmar_cita": "confirm_appointment",
    "completar_cita": "complete_appointment",
    "marcar_atendida": "complete_appointment",
    "no_se_presento": "mark_appointment_no_show",
    "no_show": "mark_appointment_no_show",
}

def _ollama_duration_ms(
    metadata: dict[str, Any],
    key: str,
) -> float | None:
    """Convierte duraciones de Ollama (nanosegundos) a ms."""
    value = metadata.get(key)

    if not isinstance(value, (int, float)):
        return None

    return value / 1_000_000

async def planner(
    state: AgentState,
) -> AgentState:
    request_id = state.get("request_id", "sin-request-id")

    planner_started_at = time.perf_counter()

    logger.info(
        "[%s] PLANNER iniciado. model=%s base_url=%s",
        request_id,
        settings.OLLAMA_MODEL,
        settings.OLLAMA_BASE_URL,
    )
    logger.info(
        "[%s] Mensaje recibido=%r",
        request_id,
        state.get("message", ""),
    )

    history_text = ""

    for item in state.get(
        "history",
        [],
    ):
        history_text += (
            f"Usuario: "
            f"{item.get('user', '')}\n"
            f"Asistente: "
            f"{item.get('assistant', '')}\n\n"
        )

    current_date = (
        datetime.now(ZoneInfo(settings.APP_TIMEZONE))
        .date()
        .isoformat()
    )

    prompt = f"""
{SYSTEM_PROMPT}

FECHA ACTUAL:

{current_date}

HISTORIAL:

{history_text or "Sin historial previo."}

MENSAJE ACTUAL:

{state.get("message", "")}
"""

    logger.debug(
        "[%s] Prompt preparado. caracteres=%s fecha=%s",
        request_id,
        len(prompt),
        current_date,
    )

    try:
        logger.info(
            "[%s] Enviando solicitud a Ollama...",
            request_id,
        )

        ollama_started_at = time.perf_counter()

        result = await llm.ainvoke(
            prompt,
        )

        ollama_elapsed_ms = elapsed_ms(ollama_started_at)

        raw_response_metadata = getattr(
            result,
            "response_metadata",
            {},
        )

        response_metadata = (
            raw_response_metadata
            if isinstance(raw_response_metadata, dict)
            else {}
        )

        logger.info(
            "[%s] [PERF] ollama.invoke wall_ms=%.2f "
            "ollama_total_ms=%s load_ms=%s prompt_eval_ms=%s "
            "eval_ms=%s prompt_tokens=%s output_tokens=%s model=%s",
            request_id,
            ollama_elapsed_ms,
            _ollama_duration_ms(
                response_metadata,
                "total_duration",
            ),
            _ollama_duration_ms(
                response_metadata,
                "load_duration",
            ),
            _ollama_duration_ms(
                response_metadata,
                "prompt_eval_duration",
            ),
            _ollama_duration_ms(
                response_metadata,
                "eval_duration",
            ),
            response_metadata.get("prompt_eval_count"),
            response_metadata.get("eval_count"),
            response_metadata.get(
                "model",
                settings.OLLAMA_MODEL,
            ),
        )

        logger.info(
            "[%s] Ollama respondió. tipo=%s",
            request_id,
            type(result).__name__,
        )
        logger.debug(
            "[%s] Respuesta cruda del LLM=\n%s",
            request_id,
            log_text(
                result.content,
                6000,
            ),
        )

        data = parser.invoke(
            result.content,
        )

        logger.debug(
            "[%s] JSON parseado=\n%s",
            request_id,
            pretty_log(
                data, 
                4000
            ),
        )

        raw_intent = str(
            data.get(
                "intent",
                "unknown",
            )
        ).strip().lower()

        intent = INTENT_ALIASES.get(
            raw_intent,
            raw_intent,
        )

        if intent not in ALLOWED_INTENTS:
            logger.warning(
                "[%s] Intent no permitido recibido=%r. "
                "Se convertirá a unknown.",
                request_id,
                intent,
            )
            intent = "unknown"

        entities = data.get(
            "entities",
            {},
        )

        if not isinstance(
            entities,
            dict,
        ):
            logger.warning(
                "[%s] entities no es un objeto. tipo=%s",
                request_id,
                type(entities).__name__,
            )
            entities = {}

        entities = normalize_entities(
            intent,
            entities,
        )

        try:
            confidence = float(
                data.get(
                    "confidence",
                    0.0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            confidence = 0.0
        
        state["intent"] = intent

        state["confidence"] = max(
            0.0,
            min(
                confidence,
                1.0,
            ),
        )

        state["entities"] = entities
        state["tool_input"] = entities

        logger.info(
            "[%s] PLANNER terminado. intent=%s confidence=%.2f\n"
            "entities=\n%s",
            request_id,
            state["intent"],
            state["confidence"],
            pretty_log(
                state["entities"],
                3000,
            ),
        )

        state["intent"] = intent
        state["confidence"] = max(
            0.0,
            min(confidence, 1.0),
        )
        state["entities"] = entities
        state["tool_input"] = entities

    except Exception as exc:
        logger.exception(
            "[%s] Falló PLANNER al comunicarse con Ollama "
            "o interpretar su respuesta. tipo=%s cadena=%s",
            request_id,
            type(exc).__name__,
            exception_chain(exc),
        )

        diagnostic_error = (
            "Planner/Ollama: "
            f"{type(exc).__name__}: {exc}"
        )

        state.setdefault(
            "errors",
            [],
        ).append(diagnostic_error)

        state["intent"] = "unknown"
        state["confidence"] = 0.0
        state["entities"] = {}
        state["tool_input"] = {}

    finally:
        logger.info(
            "[%s] [PERF] planner.total "
            "elapsed_ms=%.2f prompt_chars=%s",
            request_id,
            elapsed_ms(
                planner_started_at,
            ),
            len(prompt),
        )

    return state


def normalize_entities(
    intent: str,
    entities: dict[str, Any],
) -> dict[str, Any]:
    aliases = {
        "doctor": "doctor_name",
        "doctorName": "doctor_name",
        "medico": "doctor_name",
        "patient": "patient_name",
        "patientName": "patient_name",
        "paciente": "patient_name",
        "time": "start_time",
        "startTime": "start_time",
        "duration": "duration_minutes",
        "durationMinutes": "duration_minutes",
        "motivo": "reason",
        "appointmentId": "appointment_id",
        "cita_id": "appointment_id",
        "currentDate": "current_date",
        "oldDate": "current_date",
        "originalDate": "current_date",
        "currentStartTime": "current_start_time",
        "oldStartTime": "current_start_time",
        "originalStartTime": "current_start_time",
        "newDate": "new_date",
        "targetDate": "new_date",
        "newStartTime": "new_start_time",
        "targetStartTime": "new_start_time",
        "cancellationReason": "cancellation_reason",
        "cancelReason": "cancellation_reason",
    }

    normalized: dict[str, Any] = {}

    for key, value in entities.items():
        normalized_key = aliases.get(key, key)
        normalized[normalized_key] = value

    if intent == "search_patient":
        name = normalized.get("name") or normalized.get("patient_name")
        return {"name": str(name).strip()} if name else {}

    if intent == "reschedule_appointment":
        if not normalized.get("new_date") and normalized.get("date"):
            normalized["new_date"] = normalized.pop("date")

        if not normalized.get("new_start_time") and normalized.get("start_time"):
            normalized["new_start_time"] = normalized.pop("start_time")

    if "duration_minutes" in normalized:
        try:
            normalized["duration_minutes"] = int(
                normalized["duration_minutes"]
            )
        except (TypeError, ValueError):
            normalized.pop("duration_minutes", None)

    for boolean_key in ("upcoming", "pending"):
        if boolean_key in normalized and isinstance(
            normalized[boolean_key],
            str,
        ):
            normalized[boolean_key] = normalized[boolean_key].strip().lower() in {
                "true",
                "1",
                "yes",
                "si",
                "sí",
            }

    if "status" in normalized:
        status_aliases = {
            "programada": "scheduled",
            "programado": "scheduled",
            "pendiente": "scheduled",
            "confirmada": "confirmed",
            "confirmado": "confirmed",
            "cancelada": "cancelled",
            "cancelado": "cancelled",
            "completada": "completed",
            "completado": "completed",
            "atendida": "completed",
            "atendido": "completed",
            "no se presentó": "no_show",
            "no se presento": "no_show",
            "inasistencia": "no_show",
        }
        raw_status = str(normalized["status"]).strip().lower()
        normalized["status"] = status_aliases.get(raw_status, raw_status)

    return normalized
