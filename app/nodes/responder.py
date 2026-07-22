from app.graph.state import AgentState


async def responder(state: AgentState):

    if state["tool"] == "rag":

        state["response"] = state["tool_result"]

    else:

        state["response"] = state["tool_result"]

    state["history"].append(
        {
            "user": state["message"],
            "assistant": str(state["response"]),
        }
    )

    return state