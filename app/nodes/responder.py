from typing import Any

from app.graph.state import AgentState
from app.utils.logger import compact, get_logger, log_text


logger = get_logger("responder")

STATUS_LABELS = {
    "scheduled": "programada",
    "confirmed": "confirmada",
    "cancelled": "cancelada",
    "completed": "completada",
    "no_show": "no se presentó",
    "rescheduled": "reprogramada (estado legado)",
}


def format_patient(patient: dict[str, Any]) -> str:
    full_name = (
        f"{patient.get('firstName', '')} {patient.get('lastName', '')}"
    ).strip() or "Sin nombre"

    return (
        f"- {full_name}\n"
        f"  ID: {patient.get('_id', 'Sin ID')}\n"
        f"  Teléfono: {patient.get('phone', 'Sin teléfono')}\n"
        f"  Correo: {patient.get('email', 'Sin correo')}"
    )


def format_slots(slots: list[dict[str, Any]]) -> str:
    if not slots:
        return "No hay horarios disponibles."

    return "\n".join(
        f"- {slot.get('startTime', '--:--')} a "
        f"{slot.get('endTime', '--:--')}"
        for slot in slots
    )


def format_matches(matches: list[dict[str, Any]]) -> str:
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


def appointment_patient_name(appointment: dict[str, Any]) -> str:
    patient = appointment.get("patientId")

    if isinstance(patient, dict):
        return (
            f"{patient.get('firstName', '')} "
            f"{patient.get('lastName', '')}"
        ).strip() or "Paciente sin nombre"

    return "Paciente sin nombre"


def appointment_doctor_name(appointment: dict[str, Any]) -> str:
    doctor = appointment.get("doctorId")

    if not isinstance(doctor, dict):
        return "Médico sin nombre"

    user = doctor.get("userId")

    if isinstance(user, dict):
        return str(user.get("fullName", "Médico sin nombre"))

    return str(doctor.get("fullName", "Médico sin nombre"))


def appointment_date(appointment: dict[str, Any]) -> str:
    value = str(appointment.get("date", ""))
    return value[:10] if len(value) >= 10 else value


def format_appointment(
    appointment: dict[str, Any],
    *,
    include_reason: bool = True,
) -> str:
    status = str(appointment.get("status", ""))
    lines = [
        f"- ID: {appointment.get('_id', 'Sin ID')}",
        f"  Paciente: {appointment_patient_name(appointment)}",
        f"  Médico: {appointment_doctor_name(appointment)}",
        f"  Fecha: {appointment_date(appointment)}",
        (
            f"  Horario: {appointment.get('startTime', '--:--')} a "
            f"{appointment.get('endTime', '--:--')}"
        ),
        f"  Estado: {STATUS_LABELS.get(status, status or 'Sin estado')}",
    ]

    if include_reason:
        lines.append(f"  Motivo: {appointment.get('reason', 'Sin motivo')}")

    return "\n".join(lines)


def format_appointment_references(
    appointments: list[dict[str, Any]],
) -> str:
    return "\n\n".join(
        "- ID: {id}\n"
        "  Paciente: {patient}\n"
        "  Médico: {doctor}\n"
        "  Fecha: {date}\n"
        "  Horario: {start} a {end}\n"
        "  Estado: {status}".format(
            id=appointment.get("id", "Sin ID"),
            patient=appointment.get("patient_name", "Sin paciente"),
            doctor=appointment.get("doctor_name", "Sin médico"),
            date=appointment.get("date", "Sin fecha"),
            start=appointment.get("start_time", "--:--"),
            end=appointment.get("end_time", "--:--"),
            status=STATUS_LABELS.get(
                str(appointment.get("status", "")),
                appointment.get("status", "Sin estado"),
            ),
        )
        for appointment in appointments
    )


async def responder(
    state: AgentState,
) -> AgentState:
    request_id = state.get(
        "request_id",
        "sin-request-id",
    )

    intent = state.get(
        "intent",
        "unknown",
    )

    result = state.get(
        "tool_result",
    )

    logger.info(
        "[%s] RESPONDER iniciado. "
        "intent=%s tool=%s",
        request_id,
        intent,
        state.get("tool"),
    )

    handlers = {
        "search_patient": respond_search_patient,
        "check_appointment_availability": respond_availability,
        "schedule_appointment": respond_scheduled_appointment,
        "list_appointments": respond_list_appointments,
        "cancel_appointment": respond_cancelled_appointment,
        "reschedule_appointment": respond_rescheduled_appointment,

        "confirm_appointment": lambda value: respond_status_change(
            value,
            "La cita fue confirmada correctamente.",
        ),

        "complete_appointment": lambda value: respond_status_change(
            value,
            "La cita fue marcada como atendida.",
        ),

        "mark_appointment_no_show": lambda value: respond_status_change(
            value,
            "Se registró que el paciente no se presentó.",
        ),
    }

    handler = handlers.get(
        intent,
    )

    if handler:
        response = handler(
            result,
        )

    elif intent == "greeting":
        response = (
            "Hola. Puedo buscar pacientes, consultar disponibilidad, "
            "agendar, consultar, cancelar, reprogramar, confirmar y "
            "actualizar el estado de las citas."
        )

    elif intent == "search_document":
        response = str(
            result
            or "No encontré información en los documentos."
        )

    else:
        response = (
            "Todavía no puedo realizar esa operación. "
            "Puedo buscar pacientes y administrar citas "
            "del consultorio."
        )

    state["response"] = response

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

    logger.info(
        "[%s] RESPONDER terminó.\n"
        "response=\n%s\n"
        "errors=%s",
        request_id,
        log_text(
            state.get(
                "response",
                "",
            ),
            4000,
        ),
        compact(
            state.get(
                "errors",
                [],
            ),
            2000,
        ),
    )

    return state


def respond_search_patient(result: Any) -> str:
    if not isinstance(result, dict):
        return "No pude interpretar la respuesta del servicio de pacientes."

    if not result.get("ok"):
        return respond_tool_error(result, "No fue posible buscar al paciente.")

    patients = result.get("patients", [])
    query = result.get("query", "")

    if not patients:
        return f"No encontré pacientes que coincidan con «{query}»."

    formatted = "\n\n".join(format_patient(patient) for patient in patients)
    count = len(patients)

    return (
        f"Encontré {count} "
        f"{'paciente' if count == 1 else 'pacientes'} para «{query}»:\n\n"
        f"{formatted}"
    )


def respond_availability(result: Any) -> str:
    if not isinstance(result, dict):
        return "No pude interpretar la respuesta de disponibilidad."

    if not result.get("ok"):
        return respond_tool_error(
            result,
            "No fue posible consultar la disponibilidad.",
        )

    doctor = result.get("doctor", {})
    slots = result.get("available_slots", [])
    doctor_name = doctor.get("name", "el médico")
    date = result.get("date", "")
    duration = result.get("duration_minutes", 30)

    if not slots:
        return (
            f"{doctor_name} no tiene horarios disponibles el {date} "
            f"para citas de {duration} minutos."
        )

    return (
        f"Horarios disponibles con {doctor_name} el {date} "
        f"para citas de {duration} minutos:\n\n{format_slots(slots)}"
    )


def respond_scheduled_appointment(result: Any) -> str:
    if not isinstance(result, dict):
        return "No pude interpretar la respuesta del servicio de citas."

    if not result.get("ok"):
        return respond_tool_error(result, "No fue posible agendar la cita.")

    appointment = result.get("appointment", {})
    doctor = result.get("doctor", {})
    patient = result.get("patient", {})

    return (
        "La cita fue agendada correctamente.\n\n"
        f"Paciente: {patient.get('name', 'Sin nombre')}\n"
        f"Médico: {doctor.get('name', 'Sin nombre')}\n"
        f"Fecha: {result.get('date', '')}\n"
        f"Horario: {result.get('start_time', '')} a "
        f"{result.get('end_time', '')}\n"
        f"Motivo: {result.get('reason', '')}\n"
        f"ID de cita: {appointment.get('_id', 'Sin ID')}"
    )


def respond_list_appointments(result: Any) -> str:
    if not isinstance(result, dict):
        return "No pude interpretar la lista de citas."

    if not result.get("ok"):
        return respond_tool_error(result, "No fue posible consultar las citas.")

    appointments = result.get("appointments", [])

    if not appointments:
        return "No encontré citas con los filtros solicitados."

    count = len(appointments)
    formatted = "\n\n".join(
        format_appointment(appointment)
        for appointment in appointments
    )

    return (
        f"Encontré {count} {'cita' if count == 1 else 'citas'}:\n\n"
        f"{formatted}"
    )


def respond_cancelled_appointment(result: Any) -> str:
    if not isinstance(result, dict):
        return "No pude interpretar la cancelación de la cita."

    if not result.get("ok"):
        return respond_tool_error(result, "No fue posible cancelar la cita.")

    appointment = result.get("appointment", {})

    return (
        "La cita fue cancelada correctamente y el horario quedó liberado."
        "\n\n"
        f"{format_appointment(appointment)}\n"
        f"Motivo de cancelación: "
        f"{appointment.get('cancellationReason', 'No especificado')}"
    )


def respond_rescheduled_appointment(result: Any) -> str:
    if not isinstance(result, dict):
        return "No pude interpretar la reprogramación de la cita."

    if not result.get("ok"):
        return respond_tool_error(result, "No fue posible reprogramar la cita.")

    previous = result.get("previous_appointment", {})
    appointment = result.get("appointment", {})

    return (
        "La cita fue reprogramada correctamente. El horario anterior quedó "
        "liberado y la cita debe confirmarse nuevamente.\n\n"
        "Horario anterior:\n"
        f"- {appointment_date(previous)} de "
        f"{previous.get('startTime', '--:--')} a "
        f"{previous.get('endTime', '--:--')}\n\n"
        "Nuevo horario:\n"
        f"{format_appointment(appointment)}"
    )


def respond_status_change(result: Any, success_message: str) -> str:
    if not isinstance(result, dict):
        return "No pude interpretar la actualización de la cita."

    if not result.get("ok"):
        return respond_tool_error(
            result,
            "No fue posible actualizar el estado de la cita.",
        )

    appointment = result.get("appointment", {})
    return f"{success_message}\n\n{format_appointment(appointment)}"


def respond_tool_error(result: dict[str, Any], fallback: str) -> str:
    response = str(result.get("message", fallback))

    matches = result.get("matches", [])
    appointments = result.get("appointments", [])
    available_slots = result.get("available_slots", [])

    if matches:
        response += "\n\nCoincidencias:\n" + format_matches(matches)

    if appointments:
        response += (
            "\n\nCitas encontradas:\n"
            + format_appointment_references(appointments)
        )

    if available_slots:
        response += "\n\nHorarios disponibles:\n" + format_slots(
            available_slots
        )

    return response
