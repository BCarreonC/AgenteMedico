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


logger = get_logger("patients_tool")
api = NestAPIClient()


class PatientsTool:
    async def execute(
        self,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        name = str(
            data.get("name", "")
        ).strip()

        logger.info(
            "PatientsTool.execute data=%s name=%r",
            compact(data, 3000),
            name,
        )

        if not name:
            logger.warning(
                "PatientsTool: falta el nombre del paciente"
            )
            return {
                "ok": False,
                "error": "missing_patient_name",
                "message": (
                    "Necesito el nombre del paciente "
                    "que deseas buscar."
                ),
            }

        try:
            patients = await api.search_patients(
                name,
            )

            logger.info(
                "PatientsTool: encontrados=%s resultado=%s",
                len(patients),
                compact(patients, 6000),
            )

            return {
                "ok": True,
                "action": "search_patient",
                "query": name,
                "patients": patients,
            }

        except NestAPIError as exc:
            logger.exception(
                "PatientsTool: error NestJS cadena=%s",
                exception_chain(exc),
            )
            return {
                "ok": False,
                "error": "nest_api_error",
                "message": str(exc),
            }
