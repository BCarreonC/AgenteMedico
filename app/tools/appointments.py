import re
import asyncio
import unicodedata
from typing import Any, Awaitable, Callable

from app.services.nest_api import (
    NestAPIClient,
    NestAPIError,
)
from app.utils.logger import (
    compact,
    exception_chain,
    get_logger,
    pretty_log,
)


logger = get_logger("appointments_tool")
api = NestAPIClient()

ACTIVE_APPOINTMENT_STATUSES = {
    "scheduled",
    "confirmed",
}

VALID_APPOINTMENT_STATUSES = {
    "scheduled",
    "confirmed",
    "cancelled",
    "completed",
    "no_show",
    "rescheduled",
}


class AppointmentsTool:
    async def execute(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        action = str(data.get("action", "")).strip()

        logger.info(
            "AppointmentsTool.execute action=%s\ndata=\n%s",
            action,
            pretty_log(
                data,
                4000,
            ),
        )

        actions: dict[
            str,
            Callable[[dict[str, Any]], Awaitable[dict[str, Any]]],
        ] = {
            "check_appointment_availability": self._check_availability,
            "schedule_appointment": self._schedule_appointment,
            "list_appointments": self._list_appointments,
            "cancel_appointment": self._cancel_appointment,
            "reschedule_appointment": self._reschedule_appointment,
            "confirm_appointment": self._confirm_appointment,
            "complete_appointment": self._complete_appointment,
            "mark_appointment_no_show": self._mark_no_show,
        }

        handler = actions.get(action)

        if handler is None:
            return {
                "ok": False,
                "error": "unsupported_appointment_action",
                "message": "La operación de citas no está implementada.",
            }

        try:
            return await handler(data)

        except NestAPIError as exc:
            logger.exception(
                "AppointmentsTool: error NestJS action=%s cadena=%s",
                action,
                exception_chain(exc),
            )
            return {
                "ok": False,
                "error": "nest_api_error",
                "message": str(exc),
            }

        except Exception as exc:
            logger.exception(
                "AppointmentsTool: error no controlado action=%s cadena=%s",
                action,
                exception_chain(exc),
            )
            return {
                "ok": False,
                "error": "appointments_tool_error",
                "message": (
                    "Ocurrió un error procesando la operación de citas: "
                    f"{exc}"
                ),
            }

    async def _check_availability(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        doctor_name = str(data.get("doctor_name", "")).strip()
        date = str(data.get("date", "")).strip()

        missing_fields: list[str] = []

        if not doctor_name:
            missing_fields.append("nombre del médico")

        if not date:
            missing_fields.append("fecha")

        if missing_fields:
            return self._missing_fields(missing_fields)

        if not self._is_valid_date(date):
            return self._invalid_date()

        duration = self._get_duration(data.get("duration_minutes", 30))

        if duration is None:
            return self._invalid_duration()

        doctor, error = await self._resolve_doctor(doctor_name)

        if error:
            return error

        availability = await api.get_appointment_availability(
            doctor_id=str(doctor["_id"]),
            date=date,
            duration_minutes=duration,
        )

        return {
            "ok": True,
            "action": "check_appointment_availability",
            "doctor": {
                "id": str(doctor["_id"]),
                "name": self._doctor_name(doctor),
                "specialty": doctor.get("specialty"),
                "office": doctor.get("office"),
            },
            "date": date,
            "duration_minutes": duration,
            "schedule": availability.get("schedule", []),
            "available_slots": availability.get("availableSlots", []),
            "occupied_slots": availability.get("occupiedSlots", []),
        }

    async def _schedule_appointment(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        doctor_name = str(data.get("doctor_name", "")).strip()
        patient_name = str(data.get("patient_name", "")).strip()
        date = str(data.get("date", "")).strip()
        start_time = str(data.get("start_time", "")).strip()
        reason = str(data.get("reason", "")).strip()
        notes = str(data.get("notes", "")).strip()

        missing_fields: list[str] = []

        if not doctor_name:
            missing_fields.append("nombre del médico")
        if not patient_name:
            missing_fields.append("nombre del paciente")
        if not date:
            missing_fields.append("fecha")
        if not start_time:
            missing_fields.append("hora")
        if not reason:
            missing_fields.append("motivo de la cita")

        if missing_fields:
            return self._missing_fields(missing_fields)

        if not self._is_valid_date(date):
            return self._invalid_date()

        if not self._is_valid_time(start_time):
            return self._invalid_time()

        duration = self._get_duration(data.get("duration_minutes", 30))

        if duration is None:
            return self._invalid_duration()

        # Resolve doctor and patient concurrently
        doctor_result, patient_result = await asyncio.gather(
            self._resolve_doctor(
                doctor_name,
            ),
            self._resolve_patient(
                patient_name,
            ),
        )

        doctor, doctor_error = doctor_result
        patient, patient_error = patient_result

        if doctor_error:
            return doctor_error

        if patient_error:
            return patient_error

        availability = await api.get_appointment_availability(
            doctor_id=str(doctor["_id"]),
            date=date,
            duration_minutes=duration,
        )

        available_slots = availability.get("availableSlots", [])
        selected_slot = next(
            (
                slot
                for slot in available_slots
                if slot.get("startTime") == start_time
            ),
            None,
        )

        if selected_slot is None:
            return {
                "ok": False,
                "error": "requested_slot_unavailable",
                "message": f"El horario {start_time} no está disponible.",
                "doctor": {"name": self._doctor_name(doctor)},
                "date": date,
                "available_slots": available_slots,
            }

        body: dict[str, Any] = {
            "doctorId": str(doctor["_id"]),
            "patientId": str(patient["_id"]),
            "date": date,
            "startTime": selected_slot["startTime"],
            "endTime": selected_slot["endTime"],
            "reason": reason,
        }

        if notes:
            body["notes"] = notes

        appointment = await api.create_appointment(body)

        return {
            "ok": True,
            "action": "schedule_appointment",
            "appointment": appointment,
            "doctor": {
                "id": str(doctor["_id"]),
                "name": self._doctor_name(doctor),
            },
            "patient": {
                "id": str(patient["_id"]),
                "name": self._patient_name(patient),
            },
            "date": date,
            "start_time": selected_slot["startTime"],
            "end_time": selected_slot["endTime"],
            "reason": reason,
        }

    async def _list_appointments(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        patient_name = str(data.get("patient_name", "")).strip()
        doctor_name = str(data.get("doctor_name", "")).strip()
        date = str(data.get("date", "")).strip()
        status = str(data.get("status", "")).strip().lower()
        upcoming = self._to_bool(data.get("upcoming"))
        pending = self._to_bool(data.get("pending"))

        if date and not self._is_valid_date(date):
            return self._invalid_date()

        if status == "pending":
            pending = True
            status = ""

        if status and status not in VALID_APPOINTMENT_STATUSES:
            return {
                "ok": False,
                "error": "invalid_status",
                "message": (
                    "Estado inválido. Usa scheduled, confirmed, cancelled, "
                    "completed o no_show."
                ),
            }

        patient_id: str | None = None
        doctor_id: str | None = None

        if patient_name:
            patient, error = await self._resolve_patient(patient_name)
            if error:
                return error
            patient_id = str(patient["_id"])

        if doctor_name:
            doctor, error = await self._resolve_doctor(doctor_name)
            if error:
                return error
            doctor_id = str(doctor["_id"])

        appointments = await api.list_appointments(
            patient_id=patient_id,
            doctor_id=doctor_id,
            date=date or None,
            status=status or None,
            pending=pending if pending else None,
            upcoming=upcoming if upcoming else None,
        )

        return {
            "ok": True,
            "action": "list_appointments",
            "appointments": appointments,
            "count": len(appointments),
            "filters": {
                "patient_name": patient_name or None,
                "doctor_name": doctor_name or None,
                "date": date or None,
                "status": status or None,
                "pending": pending,
                "upcoming": upcoming,
            },
        }

    async def _cancel_appointment(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        appointment, error = await self._resolve_appointment(
            data,
            allowed_statuses=ACTIVE_APPOINTMENT_STATUSES,
        )

        if error:
            return error

        cancellation_reason = str(
            data.get("cancellation_reason", "")
        ).strip()

        updated = await api.cancel_appointment(
            str(appointment["_id"]),
            cancellation_reason or None,
        )

        return {
            "ok": True,
            "action": "cancel_appointment",
            "appointment": updated,
            "previous_appointment": appointment,
        }

    async def _reschedule_appointment(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        new_date = str(data.get("new_date", "")).strip()
        new_start_time = str(data.get("new_start_time", "")).strip()

        missing_fields: list[str] = []
        if not new_date:
            missing_fields.append("nueva fecha")
        if not new_start_time:
            missing_fields.append("nueva hora")

        if missing_fields:
            return self._missing_fields(missing_fields)

        if not self._is_valid_date(new_date):
            return self._invalid_date("La nueva fecha")

        if not self._is_valid_time(new_start_time):
            return self._invalid_time("La nueva hora")

        duration = self._get_duration(data.get("duration_minutes", 30))
        if duration is None:
            return self._invalid_duration()

        appointment, error = await self._resolve_appointment(
            data,
            allowed_statuses=ACTIVE_APPOINTMENT_STATUSES,
            date_key="current_date",
            time_key="current_start_time",
        )

        if error:
            return error

        updated = await api.reschedule_appointment(
            str(appointment["_id"]),
            date=new_date,
            start_time=new_start_time,
            duration_minutes=duration,
        )

        return {
            "ok": True,
            "action": "reschedule_appointment",
            "appointment": updated,
            "previous_appointment": appointment,
            "new_date": new_date,
            "new_start_time": new_start_time,
            "duration_minutes": duration,
        }

    async def _confirm_appointment(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._change_appointment_status(
            data,
            action="confirm_appointment",
            allowed_statuses={"scheduled"},
            operation=api.confirm_appointment,
        )

    async def _complete_appointment(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._change_appointment_status(
            data,
            action="complete_appointment",
            allowed_statuses=ACTIVE_APPOINTMENT_STATUSES,
            operation=api.complete_appointment,
        )

    async def _mark_no_show(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._change_appointment_status(
            data,
            action="mark_appointment_no_show",
            allowed_statuses=ACTIVE_APPOINTMENT_STATUSES,
            operation=api.mark_appointment_no_show,
        )

    async def _change_appointment_status(
        self,
        data: dict[str, Any],
        *,
        action: str,
        allowed_statuses: set[str],
        operation: Callable[[str], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        appointment, error = await self._resolve_appointment(
            data,
            allowed_statuses=allowed_statuses,
        )

        if error:
            return error

        updated = await operation(str(appointment["_id"]))

        return {
            "ok": True,
            "action": action,
            "appointment": updated,
            "previous_appointment": appointment,
        }

    async def _resolve_appointment(
        self,
        data: dict[str, Any],
        *,
        allowed_statuses: set[str],
        date_key: str = "date",
        time_key: str = "start_time",
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
    ]:
        appointment_id = str(data.get("appointment_id", "")).strip()

        if appointment_id:
            appointment = await api.get_appointment(appointment_id)
            status = str(appointment.get("status", ""))

            if status not in allowed_statuses:
                return None, {
                    "ok": False,
                    "error": "invalid_appointment_status",
                    "message": (
                        "La cita seleccionada tiene estado "
                        f"{status} y no admite esta operación."
                    ),
                }

            return appointment, None

        patient_name = str(data.get("patient_name", "")).strip()
        doctor_name = str(data.get("doctor_name", "")).strip()
        date = str(data.get(date_key, "")).strip()
        start_time = str(data.get(time_key, "")).strip()

        if date and not self._is_valid_date(date):
            return None, self._invalid_date()

        if start_time and not self._is_valid_time(start_time):
            return None, self._invalid_time()

        if not any([patient_name, doctor_name, date, start_time]):
            return None, self._missing_fields(
                [
                    "ID de la cita o datos para localizarla "
                    "(paciente, médico, fecha u hora)"
                ]
            )

        patient_id: str | None = None
        doctor_id: str | None = None

        if patient_name:
            patient, error = await self._resolve_patient(patient_name)
            if error:
                return None, error
            patient_id = str(patient["_id"])

        if doctor_name:
            doctor, error = await self._resolve_doctor(doctor_name)
            if error:
                return None, error
            doctor_id = str(doctor["_id"])

        appointments = await api.list_appointments(
            patient_id=patient_id,
            doctor_id=doctor_id,
            date=date or None,
            pending=True,
            upcoming=True if not date else None,
            limit=100,
        )

        appointments = [
            appointment
            for appointment in appointments
            if str(appointment.get("status", "")) in allowed_statuses
        ]

        if start_time:
            appointments = [
                appointment
                for appointment in appointments
                if appointment.get("startTime") == start_time
            ]

        if not appointments:
            return None, {
                "ok": False,
                "error": "appointment_not_found",
                "message": (
                    "No encontré una cita que coincida con los datos "
                    "proporcionados."
                ),
            }

        if len(appointments) > 1:
            return None, {
                "ok": False,
                "error": "ambiguous_appointment",
                "message": (
                    "Encontré varias citas. Indica el ID de la cita o "
                    "agrega la fecha y hora exactas."
                ),
                "appointments": [
                    self._appointment_reference(appointment)
                    for appointment in appointments
                ],
            }

        return appointments[0], None

    async def _resolve_doctor(
        self,
        name: str,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
    ]:
        doctors = await api.search_doctors(name)

        if not doctors:
            return None, {
                "ok": False,
                "error": "doctor_not_found",
                "message": f"No encontré un médico que coincida con «{name}».",
            }

        selected = self._find_exact_match(
            records=doctors,
            target=name,
            name_getter=self._doctor_name,
        )

        if selected:
            return selected, None

        if len(doctors) == 1:
            return doctors[0], None

        return None, {
            "ok": False,
            "error": "ambiguous_doctor",
            "message": "Encontré varios médicos. Indica el nombre completo.",
            "matches": [
                {
                    "id": str(doctor.get("_id", "")),
                    "name": self._doctor_name(doctor),
                    "specialty": doctor.get("specialty"),
                }
                for doctor in doctors
            ],
        }

    async def _resolve_patient(
        self,
        name: str,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
    ]:
        patients = await api.search_patients(name)

        if not patients:
            return None, {
                "ok": False,
                "error": "patient_not_found",
                "message": f"No encontré un paciente que coincida con «{name}».",
            }

        selected = self._find_exact_match(
            records=patients,
            target=name,
            name_getter=self._patient_name,
        )

        if selected:
            return selected, None

        if len(patients) == 1:
            return patients[0], None

        return None, {
            "ok": False,
            "error": "ambiguous_patient",
            "message": "Encontré varios pacientes. Indica el nombre completo.",
            "matches": [
                {
                    "id": str(patient.get("_id", "")),
                    "name": self._patient_name(patient),
                }
                for patient in patients
            ],
        }

    def _find_exact_match(
        self,
        records: list[dict[str, Any]],
        target: str,
        name_getter,
    ) -> dict[str, Any] | None:
        normalized_target = self._normalize(target)

        matches = [
            record
            for record in records
            if self._normalize(name_getter(record)) == normalized_target
        ]

        return matches[0] if len(matches) == 1 else None

    @classmethod
    def _appointment_reference(
        cls,
        appointment: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "id": str(appointment.get("_id", "")),
            "patient_name": cls._appointment_patient_name(appointment),
            "doctor_name": cls._appointment_doctor_name(appointment),
            "date": cls._appointment_date(appointment),
            "start_time": appointment.get("startTime"),
            "end_time": appointment.get("endTime"),
            "status": appointment.get("status"),
        }

    @staticmethod
    def _appointment_patient_name(
        appointment: dict[str, Any],
    ) -> str:
        patient = appointment.get("patientId")

        if isinstance(patient, dict):
            return (
                f"{patient.get('firstName', '')} "
                f"{patient.get('lastName', '')}"
            ).strip() or "Paciente sin nombre"

        return "Paciente sin nombre"

    @staticmethod
    def _appointment_doctor_name(
        appointment: dict[str, Any],
    ) -> str:
        doctor = appointment.get("doctorId")

        if isinstance(doctor, dict):
            return AppointmentsTool._doctor_name(doctor)

        return "Médico sin nombre"

    @staticmethod
    def _appointment_date(
        appointment: dict[str, Any],
    ) -> str:
        value = str(appointment.get("date", ""))
        return value[:10] if len(value) >= 10 else value

    @staticmethod
    def _doctor_name(
        doctor: dict[str, Any],
    ) -> str:
        user = doctor.get("userId")

        if isinstance(user, dict):
            return str(user.get("fullName", "Médico sin nombre"))

        return str(doctor.get("fullName", "Médico sin nombre"))

    @staticmethod
    def _patient_name(
        patient: dict[str, Any],
    ) -> str:
        return (
            f"{patient.get('firstName', '')} "
            f"{patient.get('lastName', '')}"
        ).strip() or "Paciente sin nombre"

    @staticmethod
    def _normalize(value: str) -> str:
        normalized = unicodedata.normalize("NFD", value)
        normalized = "".join(
            character
            for character in normalized
            if unicodedata.category(character) != "Mn"
        )
        return " ".join(normalized.lower().strip().split())

    @staticmethod
    def _is_valid_date(value: str) -> bool:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return False

        try:
            year, month, day = (int(part) for part in value.split("-"))
            from datetime import date

            date(year, month, day)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_valid_time(value: str) -> bool:
        return bool(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value))

    @staticmethod
    def _get_duration(value: Any) -> int | None:
        try:
            duration = int(value)
        except (TypeError, ValueError):
            return None

        return duration if 15 <= duration <= 240 else None

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "si", "sí"}

        return bool(value)

    @staticmethod
    def _missing_fields(fields: list[str]) -> dict[str, Any]:
        return {
            "ok": False,
            "error": "missing_fields",
            "message": "Falta la siguiente información: " + ", ".join(fields) + ".",
            "missing_fields": fields,
        }

    @staticmethod
    def _invalid_date(label: str = "La fecha") -> dict[str, Any]:
        return {
            "ok": False,
            "error": "invalid_date",
            "message": f"{label} debe usar el formato YYYY-MM-DD.",
        }

    @staticmethod
    def _invalid_time(label: str = "La hora") -> dict[str, Any]:
        return {
            "ok": False,
            "error": "invalid_time",
            "message": f"{label} debe usar el formato HH:mm.",
        }

    @staticmethod
    def _invalid_duration() -> dict[str, Any]:
        return {
            "ok": False,
            "error": "invalid_duration",
            "message": (
                "La duración debe ser un número entre 15 y 240 minutos."
            ),
        }
