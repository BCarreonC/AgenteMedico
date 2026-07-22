from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from app.prompts.system_prompt import SYSTEM_PROMPT
import traceback

llm = ChatOllama(
    model="qwen3:8b",
    temperature=0,
)

parser = JsonOutputParser()


async def planner(state):

    history = ""

    for item in state["history"]:
        history += (
            f"Usuario: {item['user']}\n"
            f"Asistente: {item['assistant']}\n\n"
        )

    prompt = f"""
{SYSTEM_PROMPT}

Historial:

{history}

Mensaje actual:

{state["message"]}
"""

    try:

        result = await llm.ainvoke(prompt)

        print("\n========== RESPUESTA DEL LLM ==========")
        print(result.content)
        print("=======================================\n")

        data = parser.invoke(result.content)

        state["intent"] = data.get("intent", "unknown")
        state["confidence"] = data.get("confidence", 0)
        state["entities"] = data.get("entities", {})
        state["tool_input"] = data.get("entities", {})

    except Exception as e:

        traceback.print_exc()

        state["errors"].append(str(e))

        state["intent"] = "unknown"
        state["confidence"] = 0
        state["entities"] = {}
        state["tool_input"] = {}

    return state