from app.graph.state import AgentState

from app.rag.rag_tool import RagTool

rag = RagTool()


async def rag_node(state: AgentState):

    query = state["tool_input"]["query"]

    state["tool_result"] = await rag.execute(query)

    state["tool"] = "rag"

    return state