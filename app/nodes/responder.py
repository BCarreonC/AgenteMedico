from typing import Any

from app.graph.state import AgentState
from app.utils.logger import compact, get_logger


logger = get_logger("responder")


def format_patient(
    patient: dict[str, Any],
) -> str:
    full_name = (
        f"{patient.get('firstName', '')} "
        f"{patient.get('lastName', '')}"
    ).strip() or "Sin nombre"

    return (
        f"- {full_name}\n"
        f"  ID: "
        f"{patient.get('_id', 'Sin ID')}\n"
        f"  Teléfono: "
        f"{patient.get('phone', 'Sin teléfono')}\n"
        f"  Correo: "
        f"{patient.get('email', 'Sin correo')}"
    )


def format_slots(
    slots: list[dict[str, Any]],
) -> str:
    if not slots:
        return "No hay horarios disponibles."

    return "\n".join(
        (
            f"- {slot.get('startTime', '--:--')} "
            f"a {slot.get('endTime', '--:--')}"
        )
        for slot in slots
    )


def format_matches(
    matches: list[dict[str, Any]],
) -> str:
    if not matches:
        return ""

    return "\n".join(
        (
            f"- {match.get('name', 'Sin nombre')}"
            + (
                f" — {match.get('specialty')}"
                if match.get("specialty")
                else ""
            )
        )
        for match in matches
    )


async def responder(
    state: AgentState,
) -> AgentState:
    request_id = state.get("request_id", "sin-request-id")

    intent = state.get(
        "intent",
        "unknown",
    )

    result = state.get(
        "tool_result",
    )

    logger.info(
        "[%s] RESPONDER iniciado. intent=%s tool=%s result=%s",
        request_id,
        intent,
        state.get("tool"),
        compact(result, 6000),
    )

    if intent == "search_patient":
        response = respond_search_patient(
            result,
        )

    elif (
        intent ==
        "check_appointment_availability"
    ):
        response = respond_availability(
            result,
        )

    elif intent == "schedule_appointment":
        response = respond_scheduled_appointment(
            result,
        )

    elif intent == "greeting":
        response = (
            "Hola. Puedo buscar pacientes, "
            "consultar disponibilidad de médicos "
            "y agendar citas."
        )

    elif intent == "search_document":
        response = str(
            result
            or (
                "No encontré información "
                "en los documentos."
            )
        )

    else:
        response = (
            "Todavía no puedo realizar esa operación. "
            "Puedo buscar pacientes, consultar "
            "disponibilidad y agendar citas."
        )

    state["response"] = response

    logger.info(
        "[%s] RESPONDER terminó. response=%r errors=%s",
        request_id,
        response,
        state.get("errors", []),
    )

    state.setdefault(
        "history",
        [],
    ).append(
        {
            "user": state.get(
                "message",
                "",
            ),
            "assistant": response,
        }
    )

    return state


def respond_search_patient(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return (
            "No pude interpretar la respuesta "
            "del servicio de pacientes."
        )

    if not result.get("ok"):
        return str(
            result.get(
                "message",
                "No fue posible buscar al paciente.",
            )
        )

    patients = result.get(
        "patients",
        [],
    )

    query = result.get(
        "query",
        "",
    )

    if not patients:
        return (
            "No encontré pacientes que "
            f"coincidan con «{query}»."
        )

    formatted = "\n\n".join(
        format_patient(patient)
        for patient in patients
    )

    count = len(patients)

    return (
        f"Encontré {count} "
        f"{'paciente' if count == 1 else 'pacientes'} "
        f"para «{query}»:\n\n"
        f"{formatted}"
    )


def respond_availability(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return (
            "No pude interpretar la respuesta "
            "de disponibilidad."
        )

    if not result.get("ok"):
        response = str(
            result.get(
                "message",
                "No fue posible consultar "
                "la disponibilidad.",
            )
        )

        matches = result.get(
            "matches",
            [],
        )

        if matches:
            response += (
                "\n\nCoincidencias:\n"
                + format_matches(matches)
            )

        return response

    doctor = result.get(
        "doctor",
        {},
    )

    slots = result.get(
        "available_slots",
        [],
    )

    doctor_name = doctor.get(
        "name",
        "el médico",
    )

    date = result.get(
        "date",
        "",
    )

    duration = result.get(
        "duration_minutes",
        30,
    )

    if not slots:
        return (
            f"{doctor_name} no tiene horarios "
            f"disponibles el {date} para citas "
            f"de {duration} minutos."
        )

    return (
        f"Horarios disponibles con "
        f"{doctor_name} el {date} "
        f"para citas de {duration} minutos:\n\n"
        f"{format_slots(slots)}"
    )


def respond_scheduled_appointment(
    result: Any,
) -> str:
    if not isinstance(
        result,
        dict,
    ):
        return (
            "No pude interpretar la respuesta "
            "del servicio de citas."
        )

    if not result.get("ok"):
        response = str(
            result.get(
                "message",
                "No fue posible agendar la cita.",
            )
        )

        matches = result.get(
            "matches",
            [],
        )

        available_slots = result.get(
            "available_slots",
            [],
        )

        if matches:
            response += (
                "\n\nCoincidencias:\n"
                + format_matches(matches)
            )

        if available_slots:
            response += (
                "\n\nHorarios disponibles:\n"
                + format_slots(
                    available_slots,
                )
            )

        return response

    appointment = result.get(
        "appointment",
        {},
    )

    doctor = result.get(
        "doctor",
        {},
    )

    patient = result.get(
        "patient",
        {},
    )

    return (
        "La cita fue agendada correctamente.\n\n"
        f"Paciente: "
        f"{patient.get('name', 'Sin nombre')}\n"
        f"Médico: "
        f"{doctor.get('name', 'Sin nombre')}\n"
        f"Fecha: {result.get('date', '')}\n"
        f"Horario: "
        f"{result.get('start_time', '')} a "
        f"{result.get('end_time', '')}\n"
        f"Motivo: {result.get('reason', '')}\n"
        f"ID de cita: "
        f"{appointment.get('_id', 'Sin ID')}"
    )