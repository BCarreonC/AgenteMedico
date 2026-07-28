import re
import unicodedata
from typing import Any

from app.services.nest_api import (
    NestAPIClient,
    NestAPIError,
)
from app.utils.logger import (
    compact,
    exception_chain,
    get_logger,
)


logger = get_logger("appointments_tool")
api = NestAPIClient()


class AppointmentsTool:
    async def execute(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        action = str(
            data.get("action", "")
        ).strip()

        logger.info(
            "AppointmentsTool.execute action=%s data=%s",
            action,
            compact(data, 5000),
        )

        try:
            if (
                action ==
                "check_appointment_availability"
            ):
                return await self._check_availability(
                    data,
                )

            if action == "schedule_appointment":
                return await self._schedule_appointment(
                    data,
                )

            return {
                "ok": False,
                "error":
                    "unsupported_appointment_action",
                "message":
                    "La operación de citas no está implementada.",
            }

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
                    "Ocurrió un error procesando "
                    f"la cita: {exc}"
                ),
            }

    async def _check_availability(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        doctor_name = str(
            data.get("doctor_name", "")
        ).strip()

        date = str(
            data.get("date", "")
        ).strip()

        logger.info(
            "Check availability doctor=%r date=%r raw_duration=%r",
            doctor_name,
            date,
            data.get("duration_minutes", 30),
        )

        missing_fields: list[str] = []

        if not doctor_name:
            missing_fields.append(
                "nombre del médico",
            )

        if not date:
            missing_fields.append(
                "fecha",
            )

        if missing_fields:
            return self._missing_fields(
                missing_fields,
            )

        if not self._is_valid_date(date):
            return {
                "ok": False,
                "error": "invalid_date",
                "message": (
                    "La fecha debe usar el formato "
                    "YYYY-MM-DD."
                ),
            }

        duration = self._get_duration(
            data.get("duration_minutes", 30),
        )

        if duration is None:
            return {
                "ok": False,
                "error": "invalid_duration",
                "message": (
                    "La duración debe ser un número "
                    "entre 15 y 240 minutos."
                ),
            }

        doctor, error = (
            await self._resolve_doctor(
                doctor_name,
            )
        )

        if error:
            logger.warning(
                "Check availability: no se resolvió médico error=%s",
                compact(error, 3000),
            )
            return error

        logger.info(
            "Check availability: médico resuelto id=%s name=%s",
            doctor.get("_id"),
            self._doctor_name(doctor),
        )

        availability = (
            await api
            .get_appointment_availability(
                doctor_id=str(
                    doctor["_id"],
                ),
                date=date,
                duration_minutes=duration,
            )
        )

        logger.info(
            "Check availability: respuesta NestJS=%s",
            compact(availability, 7000),
        )

        return {
            "ok": True,
            "action":
                "check_appointment_availability",
            "doctor": {
                "id": str(
                    doctor["_id"],
                ),
                "name":
                    self._doctor_name(
                        doctor,
                    ),
                "specialty":
                    doctor.get(
                        "specialty",
                    ),
                "office":
                    doctor.get(
                        "office",
                    ),
            },
            "date": date,
            "duration_minutes": duration,
            "schedule":
                availability.get(
                    "schedule",
                    [],
                ),
            "available_slots":
                availability.get(
                    "availableSlots",
                    [],
                ),
            "occupied_slots":
                availability.get(
                    "occupiedSlots",
                    [],
                ),
        }

    async def _schedule_appointment(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        doctor_name = str(
            data.get("doctor_name", "")
        ).strip()

        patient_name = str(
            data.get("patient_name", "")
        ).strip()

        date = str(
            data.get("date", "")
        ).strip()

        start_time = str(
            data.get("start_time", "")
        ).strip()

        reason = str(
            data.get("reason", "")
        ).strip()

        notes = str(
            data.get("notes", "")
        ).strip()

        logger.info(
            "Schedule appointment doctor=%r patient=%r date=%r start=%r reason=%r duration=%r",
            doctor_name,
            patient_name,
            date,
            start_time,
            reason,
            data.get("duration_minutes", 30),
        )

        missing_fields: list[str] = []

        if not doctor_name:
            missing_fields.append(
                "nombre del médico",
            )

        if not patient_name:
            missing_fields.append(
                "nombre del paciente",
            )

        if not date:
            missing_fields.append(
                "fecha",
            )

        if not start_time:
            missing_fields.append(
                "hora",
            )

        if not reason:
            missing_fields.append(
                "motivo de la cita",
            )

        if missing_fields:
            return self._missing_fields(
                missing_fields,
            )

        if not self._is_valid_date(date):
            return {
                "ok": False,
                "error": "invalid_date",
                "message": (
                    "La fecha debe usar el formato "
                    "YYYY-MM-DD."
                ),
            }

        if not self._is_valid_time(
            start_time,
        ):
            return {
                "ok": False,
                "error": "invalid_time",
                "message": (
                    "La hora debe usar el formato "
                    "HH:mm."
                ),
            }

        duration = self._get_duration(
            data.get("duration_minutes", 30),
        )

        if duration is None:
            return {
                "ok": False,
                "error": "invalid_duration",
                "message": (
                    "La duración debe ser un número "
                    "entre 15 y 240 minutos."
                ),
            }

        doctor, doctor_error = (
            await self._resolve_doctor(
                doctor_name,
            )
        )

        if doctor_error:
            logger.warning(
                "Schedule appointment: error resolviendo médico=%s",
                compact(doctor_error, 3000),
            )
            return doctor_error

        logger.info(
            "Schedule appointment: médico id=%s name=%s",
            doctor.get("_id"),
            self._doctor_name(doctor),
        )

        patient, patient_error = (
            await self._resolve_patient(
                patient_name,
            )
        )

        if patient_error:
            logger.warning(
                "Schedule appointment: error resolviendo paciente=%s",
                compact(patient_error, 3000),
            )
            return patient_error

        logger.info(
            "Schedule appointment: paciente id=%s name=%s",
            patient.get("_id"),
            self._patient_name(patient),
        )

        availability = (
            await api
            .get_appointment_availability(
                doctor_id=str(
                    doctor["_id"],
                ),
                date=date,
                duration_minutes=duration,
            )
        )

        logger.info(
            "Schedule appointment: disponibilidad recibida=%s",
            compact(availability, 7000),
        )

        available_slots = (
            availability.get(
                "availableSlots",
                [],
            )
        )

        selected_slot = next(
            (
                slot
                for slot in available_slots
                if slot.get("startTime")
                == start_time
            ),
            None,
        )

        if selected_slot is None:
            logger.warning(
                "Schedule appointment: slot solicitado %s no disponible. slots=%s",
                start_time,
                compact(available_slots, 5000),
            )
            return {
                "ok": False,
                "error":
                    "requested_slot_unavailable",
                "message": (
                    f"El horario {start_time} "
                    "no está disponible."
                ),
                "doctor": {
                    "name":
                        self._doctor_name(
                            doctor,
                        ),
                },
                "date": date,
                "available_slots":
                    available_slots,
            }

        body: dict[str, Any] = {
            "doctorId": str(
                doctor["_id"],
            ),
            "patientId": str(
                patient["_id"],
            ),
            "date": date,
            "startTime":
                selected_slot["startTime"],
            "endTime":
                selected_slot["endTime"],
            "reason": reason,
        }

        if notes:
            body["notes"] = notes

        logger.info(
            "Schedule appointment: creando cita body=%s",
            compact(body, 4000),
        )

        appointment = (
            await api.create_appointment(
                body,
            )
        )

        logger.info(
            "Schedule appointment: cita creada=%s",
            compact(appointment, 7000),
        )

        return {
            "ok": True,
            "action": "schedule_appointment",
            "appointment": appointment,
            "doctor": {
                "id": str(
                    doctor["_id"],
                ),
                "name":
                    self._doctor_name(
                        doctor,
                    ),
            },
            "patient": {
                "id": str(
                    patient["_id"],
                ),
                "name":
                    self._patient_name(
                        patient,
                    ),
            },
            "date": date,
            "start_time":
                selected_slot["startTime"],
            "end_time":
                selected_slot["endTime"],
            "reason": reason,
        }

    async def _resolve_doctor(
        self,
        name: str,
    ) -> tuple[
        dict[str, Any] | None,
        dict[str, Any] | None,
    ]:
        logger.info(
            "Resolviendo médico name=%r",
            name,
        )

        doctors = await api.search_doctors(
            name,
        )

        logger.info(
            "Búsqueda de médicos devolvió %s resultados=%s",
            len(doctors),
            compact(doctors, 6000),
        )

        if not doctors:
            return None, {
                "ok": False,
                "error": "doctor_not_found",
                "message": (
                    "No encontré un médico "
                    f"que coincida con «{name}»."
                ),
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
            "message": (
                "Encontré varios médicos. "
                "Indica el nombre completo."
            ),
            "matches": [
                {
                    "id": str(
                        doctor.get("_id", ""),
                    ),
                    "name":
                        self._doctor_name(
                            doctor,
                        ),
                    "specialty":
                        doctor.get(
                            "specialty",
                        ),
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
        logger.info(
            "Resolviendo paciente name=%r",
            name,
        )

        patients = await api.search_patients(
            name,
        )

        logger.info(
            "Búsqueda de pacientes devolvió %s resultados=%s",
            len(patients),
            compact(patients, 6000),
        )

        if not patients:
            return None, {
                "ok": False,
                "error": "patient_not_found",
                "message": (
                    "No encontré un paciente "
                    f"que coincida con «{name}»."
                ),
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
            "message": (
                "Encontré varios pacientes. "
                "Indica el nombre completo."
            ),
            "matches": [
                {
                    "id": str(
                        patient.get("_id", ""),
                    ),
                    "name":
                        self._patient_name(
                            patient,
                        ),
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
        normalized_target = (
            self._normalize(target)
        )

        matches = [
            record
            for record in records
            if self._normalize(
                name_getter(record),
            ) == normalized_target
        ]

        if len(matches) == 1:
            return matches[0]

        return None

    @staticmethod
    def _doctor_name(
        doctor: dict[str, Any],
    ) -> str:
        user = doctor.get("userId")

        if isinstance(user, dict):
            return str(
                user.get(
                    "fullName",
                    "Médico sin nombre",
                )
            )

        return str(
            doctor.get(
                "fullName",
                "Médico sin nombre",
            )
        )

    @staticmethod
    def _patient_name(
        patient: dict[str, Any],
    ) -> str:
        return (
            f"{patient.get('firstName', '')} "
            f"{patient.get('lastName', '')}"
        ).strip() or "Paciente sin nombre"

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        normalized = unicodedata.normalize(
            "NFD",
            value,
        )

        normalized = "".join(
            character
            for character in normalized
            if unicodedata.category(
                character,
            ) != "Mn"
        )

        return " ".join(
            normalized
            .lower()
            .strip()
            .split()
        )

    @staticmethod
    def _is_valid_date(
        value: str,
    ) -> bool:
        return bool(
            re.fullmatch(
                r"\d{4}-\d{2}-\d{2}",
                value,
            )
        )

    @staticmethod
    def _is_valid_time(
        value: str,
    ) -> bool:
        return bool(
            re.fullmatch(
                r"(?:[01]\d|2[0-3]):[0-5]\d",
                value,
            )
        )

    @staticmethod
    def _get_duration(
        value: Any,
    ) -> int | None:
        try:
            duration = int(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

        if not 15 <= duration <= 240:
            return None

        return duration

    @staticmethod
    def _missing_fields(
        fields: list[str],
    ) -> dict[str, Any]:
        return {
            "ok": False,
            "error": "missing_fields",
            "message": (
                "Falta la siguiente información: "
                + ", ".join(fields)
                + "."
            ),
            "missing_fields": fields,
        }