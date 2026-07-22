from langgraph.graph import StateGraph, END

from app.graph.state import AgentState

from app.nodes.planner import planner
from app.nodes.router import router
from app.nodes.responder import responder
from app.nodes.rag_node import rag_node

from app.tools.patients import PatientsTool
from app.tools.appointments import AppointmentsTool
from app.tools.consultations import ConsultationsTool
from app.tools.notifications import NotificationsTool

from app.memory.memory import memory


patients = PatientsTool()
appointments = AppointmentsTool()
consultations = ConsultationsTool()
notifications = NotificationsTool()


async def tool_node(state: AgentState):

    if state["tool"] == "patients":
        state["tool_result"] = await patients.execute(state["tool_input"])

    elif state["tool"] == "appointments":
        state["tool_result"] = await appointments.execute(state["tool_input"])

    elif state["tool"] == "consultations":
        state["tool_result"] = await consultations.execute(state["tool_input"])

    elif state["tool"] == "notifications":
        state["tool_result"] = await notifications.execute(state["tool_input"])

    else:
        state["tool_result"] = "Herramienta no encontrada."

    return state


def route(state: AgentState):

    if state["tool"] == "rag":
        return "rag"

    return "tool"


builder = StateGraph(AgentState)

builder.add_node("planner", planner)
builder.add_node("router", router)
builder.add_node("tool", tool_node)
builder.add_node("rag", rag_node)
builder.add_node("responder", responder)

builder.set_entry_point("planner")

builder.add_edge("planner", "router")

builder.add_conditional_edges(
    "router",
    route,
    {
        "tool": "tool",
        "rag": "rag",
    },
)

builder.add_edge("tool", "responder")
builder.add_edge("rag", "responder")
builder.add_edge("responder", END)

graph = builder.compile(
    checkpointer=memory,
)