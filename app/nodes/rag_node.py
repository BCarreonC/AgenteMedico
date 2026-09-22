import time

from app.graph.state import AgentState
from app.rag.rag_tool import RagTool
from app.utils.logger import elapsed_ms, get_logger


logger = get_logger("rag_node")

rag = RagTool()


async def rag_node(state: AgentState):
    request_id = state.get(
        "request_id",
        "sin-request-id",
    )

    started_at = time.perf_counter()

    query = state["tool_input"]["query"]

    try:
        state["tool_result"] = await rag.execute(query)
        state["tool"] = "rag"

    finally:
        logger.info(
            "[%s] [PERF] tool.execute elapsed_ms=%.2f "
            "tool=rag intent=%s",
            request_id,
            elapsed_ms(started_at),
            state.get("intent"),
        )

    return state