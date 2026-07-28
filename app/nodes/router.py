from app.graph.state import AgentState
from app.utils.logger import get_logger


logger = get_logger("router")


async def router(
    state: AgentState,
) -> AgentState:
    request_id = state.get("request_id", "sin-request-id")
    intent = state.get("intent", "")

    routes = {
        "search_patient": "patients",
        "check_appointment_availability":
            "appointments",
        "schedule_appointment":
            "appointments",
        "search_document": "rag",
    }

    selected_tool = routes.get(intent)
    state["tool"] = selected_tool

    logger.info(
        "[%s] ROUTER intent=%s -> tool=%s",
        request_id,
        intent,
        selected_tool,
    )

    if selected_tool is None:
        logger.warning(
            "[%s] ROUTER no encontró herramienta para intent=%s. "
            "errors=%s",
            request_id,
            intent,
            state.get("errors", []),
        )

    return state
