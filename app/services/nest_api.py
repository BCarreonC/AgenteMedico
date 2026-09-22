import time
from typing import Any

import httpx

from app.config.settings import settings
from app.utils.logger import (
    compact,
    exception_chain,
    get_logger,
    elapsed_ms,
    get_request_id,
    log_text,
    pretty_log,
)


logger = get_logger("nest_api")


class NestAPIError(RuntimeError):
    """Error controlado al consumir NestJS."""


class NestAPIClient:
    def __init__(self) -> None:
        self.base_url = settings.NEST_API.rstrip("/")
        self.timeout = 15.0

        logger.info(
            "NestAPIClient configurado base_url=%s timeout=%ss",
            self.base_url,
            self.timeout,
        )

    async def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        return await self._request(
            "GET",
            endpoint,
            params=params,
        )

    async def post(
        self,
        endpoint: str,
        body: dict[str, Any],
    ) -> Any:
        return await self._request(
            "POST",
            endpoint,
            body=body,
        )

    async def patch(
        self,
        endpoint: str,
        body: dict[str, Any] | None = None,
    ) -> Any:
        return await self._request(
            "PATCH",
            endpoint,
            body=body or {},
        )

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        url = self._build_url(endpoint)

        request_id = get_request_id()
        started_at = time.perf_counter()

        status: int | str = "not_sent"

        logger.info(
            "HTTP %s %s\nparams=\n%s\nbody=\n%s",
            method,
            url,
            pretty_log(
                params or {},
                2000,
            ),
            pretty_log(
                body or {},
                5000,
            ),
        )
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
            ) as client:
                response = await client.request(
                    method,
                    url,
                    params=params,
                    json=body if body is not None else None,
                )

            status = response.status_code

            logger.info(
                "HTTP %s %s -> status=%s",
                method,
                str(response.request.url),
                response.status_code,
            )

            try:
                debug_body = response.json()
        
            except ValueError:
                debug_body = response.text

            logger.debug(
                "HTTP %s response body:\n%s",
                method,
                pretty_log(
                    debug_body,
                    7000,
                ),
            )

            response.raise_for_status()

            if response.status_code == 204 or not response.content:
                return None

            return response.json()

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code

            detail = self._get_error_detail(
                exc.response,
            )

            logger.error(
                "NestJS respondió con error. method=%s url=%s "
                "status=%s detail=%s",
                method,
                exc.request.url,
                exc.response.status_code,
                detail,
            )

            raise NestAPIError(
                f"NestJS respondió "
                f"{exc.response.status_code}: "
                f"{detail}"
            ) from exc

        except httpx.RequestError as exc:
            status = "network_error"

            logger.exception(
                "Error de conexión con NestJS. method=%s url=%s cadena=%s",
                method,
                url,
                exception_chain(exc),
            )

            raise NestAPIError(
                "No fue posible conectar con "
                f"NestJS en {self.base_url}."
            ) from exc

        except ValueError as exc:
            status = (
                status
                if status != "not_sent"
                else "invalid_json"
            )

            logger.exception(
                "NestJS respondió contenido que no es JSON. "
                "method=%s url=%s cadena=%s",
                method,
                url,
                exception_chain(exc),
            )

            raise NestAPIError(
                "NestJS devolvió una respuesta que no es JSON."
            ) from exc

        finally:
            logger.info(
                "[%s] [PERF] http.nest elapsed_ms=%.2f "
                "method=%s endpoint=%s status=%s",
                request_id,
                elapsed_ms(started_at),
                method,
                endpoint,
                status,
            )

    async def search_patients(
        self,
        name: str,
    ) -> list[dict[str, Any]]:
        result = await self.get(
            "/patients/search",
            params={"name": name},
        )
        return self._expect_list(result, "La búsqueda de pacientes")

    async def search_doctors(
        self,
        name: str,
    ) -> list[dict[str, Any]]:
        result = await self.get(
            "/doctors/search",
            params={"name": name},
        )
        return self._expect_list(result, "La búsqueda de médicos")

    async def get_appointment_availability(
        self,
        doctor_id: str,
        date: str,
        duration_minutes: int = 30,
    ) -> dict[str, Any]:
        result = await self.get(
            "/appointments/availability",
            params={
                "doctorId": doctor_id,
                "date": date,
                "durationMinutes": duration_minutes,
            },
        )
        return self._expect_dict(result, "La disponibilidad")

    async def create_appointment(
        self,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        result = await self.post(
            "/appointments",
            body,
        )
        return self._expect_dict(result, "La creación de la cita")

    async def list_appointments(
        self,
        *,
        patient_id: str | None = None,
        doctor_id: str | None = None,
        date: str | None = None,
        status: str | None = None,
        pending: bool | None = None,
        upcoming: bool | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}

        optional_params = {
            "patientId": patient_id,
            "doctorId": doctor_id,
            "date": date,
            "status": status,
            "pending": pending,
            "upcoming": upcoming,
        }

        params.update(
            {
                key: value
                for key, value in optional_params.items()
                if value is not None
            }
        )

        result = await self.get(
            "/appointments",
            params=params,
        )
        return self._expect_list(result, "La consulta de citas")

    async def get_appointment(
        self,
        appointment_id: str,
    ) -> dict[str, Any]:
        result = await self.get(
            f"/appointments/{appointment_id}",
        )
        return self._expect_dict(result, "La consulta de la cita")

    async def cancel_appointment(
        self,
        appointment_id: str,
        cancellation_reason: str | None = None,
    ) -> dict[str, Any]:
        body = {}
        if cancellation_reason:
            body["cancellationReason"] = cancellation_reason

        result = await self.patch(
            f"/appointments/{appointment_id}/cancel",
            body,
        )
        return self._expect_dict(result, "La cancelación de la cita")

    async def reschedule_appointment(
        self,
        appointment_id: str,
        *,
        date: str,
        start_time: str,
        duration_minutes: int,
    ) -> dict[str, Any]:
        result = await self.patch(
            f"/appointments/{appointment_id}/reschedule",
            {
                "date": date,
                "startTime": start_time,
                "durationMinutes": duration_minutes,
            },
        )
        return self._expect_dict(result, "La reprogramación de la cita")

    async def confirm_appointment(
        self,
        appointment_id: str,
    ) -> dict[str, Any]:
        result = await self.patch(
            f"/appointments/{appointment_id}/confirm",
        )
        return self._expect_dict(result, "La confirmación de la cita")

    async def complete_appointment(
        self,
        appointment_id: str,
    ) -> dict[str, Any]:
        result = await self.patch(
            f"/appointments/{appointment_id}/complete",
        )
        return self._expect_dict(result, "La finalización de la cita")

    async def mark_appointment_no_show(
        self,
        appointment_id: str,
    ) -> dict[str, Any]:
        result = await self.patch(
            f"/appointments/{appointment_id}/no-show",
        )
        return self._expect_dict(result, "El registro de inasistencia")

    def _build_url(
        self,
        endpoint: str,
    ) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    @staticmethod
    def _expect_list(
        result: Any,
        operation: str,
    ) -> list[dict[str, Any]]:
        if not isinstance(result, list):
            raise NestAPIError(
                f"{operation} devolvió un formato inesperado."
            )

        return result

    @staticmethod
    def _expect_dict(
        result: Any,
        operation: str,
    ) -> dict[str, Any]:
        if not isinstance(result, dict):
            raise NestAPIError(
                f"{operation} devolvió un formato inesperado."
            )

        return result

    @staticmethod
    def _get_error_detail(
        response: httpx.Response,
    ) -> str:
        try:
            payload = response.json()

            if isinstance(payload, dict):
                message = payload.get("message")

                if isinstance(message, list):
                    return "; ".join(str(item) for item in message)

                if message:
                    return str(message)

            return str(payload)

        except ValueError:
            return response.text or "Error sin detalle"
