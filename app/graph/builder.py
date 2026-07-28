from langgraph.graph import END, StateGraph

from app.graph.state import AgentState
from app.memory.memory import memory
from app.nodes.planner import planner
from app.nodes.rag_node import rag_node
from app.nodes.responder import responder
from app.nodes.router import router
from app.tools.appointments import AppointmentsTool
from app.tools.patients import PatientsTool
from app.utils.logger import compact, get_logger


logger = get_logger("graph")

patients = PatientsTool()
appointments = AppointmentsTool()


async def tool_node(
    state: AgentState,
) -> AgentState:
    request_id = state.get("request_id", "sin-request-id")
    tool = state.get("tool")

    tool_input = {
        **state.get(
            "tool_input",
            {},
        ),
        "action": state.get(
            "intent",
            "",
        ),
    }

    logger.info(
        "[%s] TOOL_NODE iniciado. tool=%s input=%s",
        request_id,
        tool,
        compact(tool_input, 4000),
    )

    if tool == "patients":
        state["tool_result"] = (
            await patients.execute(
                state.get(
                    "tool_input",
                    {},
                )
            )
        )

    elif tool == "appointments":
        state["tool_result"] = (
            await appointments.execute(
                tool_input,
            )
        )

    else:
        state["tool_result"] = {
            "ok": False,
            "message": "Herramienta no encontrada.",
        }

    logger.info(
        "[%s] TOOL_NODE terminado. result=%s",
        request_id,
        compact(state.get("tool_result"), 7000),
    )

    return state


def route_after_router(
    state: AgentState,
) -> str:
    request_id = state.get("request_id", "sin-request-id")
    tool = state.get("tool")

    if tool == "rag":
        route = "rag"
    elif tool in {
        "patients",
        "appointments",
    }:
        route = "tool"
    else:
        route = "responder"

    logger.info(
        "[%s] GRAPH route_after_router tool=%s -> node=%s",
        request_id,
        tool,
        route,
    )

    return route


builder = StateGraph(
    AgentState,
)

builder.add_node(
    "planner",
    planner,
)
builder.add_node(
    "router",
    router,
)
builder.add_node(
    "tool",
    tool_node,
)
builder.add_node(
    "rag",
    rag_node,
)
builder.add_node(
    "responder",
    responder,
)

builder.set_entry_point(
    "planner",
)

builder.add_edge(
    "planner",
    "router",
)

builder.add_conditional_edges(
    "router",
    route_after_router,
    {
        "tool": "tool",
        "rag": "rag",
        "responder": "responder",
    },
)

builder.add_edge(
    "tool",
    "responder",
)
builder.add_edge(
    "rag",
    "responder",
)
builder.add_edge(
    "responder",
    END,
)

graph = builder.compile(
    checkpointer=memory,
)
