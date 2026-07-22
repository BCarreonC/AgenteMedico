from app.graph.state import AgentState


async def router(state: AgentState):

    routes = {

        "search_patient":"patients",

        "create_patient":"patients",

        "schedule_appointment":"appointments",

        "cancel_appointment":"appointments",

        "reschedule_appointment":"appointments",

        "create_consultation":"consultations",

        "search_consultation":"consultations",

        "send_notification":"notifications",

        "search_document":"rag"

    }

    state["tool"] = routes.get(state["intent"])

    return state