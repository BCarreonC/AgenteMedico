from fastapi import FastAPI

import uuid

from app.schemas.request import ChatRequest

from app.graph.builder import graph


app = FastAPI()


@app.post("/chat")
async def chat(request: ChatRequest):

    state = {

        "message": request.message,

        "history": [],

        "intent": "",

        "confidence": 0,

        "entities": {},

        "tool": None,

        "tool_input": {},

        "tool_result": None,

        "response": "",

        "errors": []

    }

    result = await graph.ainvoke(

    state,

    config={

        "configurable":{

            "thread_id":request.session_id

        }

    }

)

    return {

    "intent": result["intent"],

    "tool": result["tool"],

    "response": result["response"]

    }