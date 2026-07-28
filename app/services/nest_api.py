from typing import Any

import httpx

from app.config.settings import settings
from app.utils.logger import (
    compact,
    exception_chain,
    get_logger,
)


logger = get_logger("nest_api")


class NestAPIError(RuntimeError):
    """Error controlado al consumir NestJS."""


class NestAPIClient:
    def __init__(self) -> None:
        self.base_url = (
            settings.NEST_API.rstrip("/")
        )
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
        url = self._build_url(endpoint)

        logger.info(
            "HTTP GET %s params=%s",
            url,
            compact(params or {}, 2000),
        )

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
            ) as client:
                response = await client.get(
                    url,
                    params=params,
                )

            logger.info(
                "HTTP GET %s -> status=%s",
                str(response.request.url),
                response.status_code,
            )
            logger.debug(
                "HTTP GET response body=%s",
                compact(response.text, 6000),
            )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as exc:
            detail = self._get_error_detail(
                exc.response,
            )

            logger.error(
                "NestJS respondió con error. url=%s status=%s "
                "detail=%s",
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
            logger.exception(
                "Error de conexión con NestJS. url=%s cadena=%s",
                url,
                exception_chain(exc),
            )

            raise NestAPIError(
                "No fue posible conectar con "
                f"NestJS en {self.base_url}."
            ) from exc

        except ValueError as exc:
            logger.exception(
                "NestJS respondió contenido que no es JSON. "
                "url=%s cadena=%s",
                url,
                exception_chain(exc),
            )
            raise NestAPIError(
                "NestJS devolvió una respuesta que no es JSON."
            ) from exc

    async def post(
        self,
        endpoint: str,
        body: dict[str, Any],
    ) -> Any:
        url = self._build_url(endpoint)

        logger.info(
            "HTTP POST %s body=%s",
            url,
            compact(body, 5000),
        )

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
            ) as client:
                response = await client.post(
                    url,
                    json=body,
                )

            logger.info(
                "HTTP POST %s -> status=%s",
                str(response.request.url),
                response.status_code,
            )
            logger.debug(
                "HTTP POST response body=%s",
                compact(response.text, 6000),
            )

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as exc:
            detail = self._get_error_detail(
                exc.response,
            )

            logger.error(
                "NestJS respondió con error. url=%s status=%s "
                "detail=%s",
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
            logger.exception(
                "Error de conexión con NestJS. url=%s cadena=%s",
                url,
                exception_chain(exc),
            )

            raise NestAPIError(
                "No fue posible conectar con "
                f"NestJS en {self.base_url}."
            ) from exc

        except ValueError as exc:
            logger.exception(
                "NestJS respondió contenido que no es JSON. "
                "url=%s cadena=%s",
                url,
                exception_chain(exc),
            )
            raise NestAPIError(
                "NestJS devolvió una respuesta que no es JSON."
            ) from exc

    async def search_patients(
        self,
        name: str,
    ) -> list[dict[str, Any]]:
        result = await self.get(
            "/patients/search",
            params={
                "name": name,
            },
        )

        if not isinstance(result, list):
            raise NestAPIError(
                "La búsqueda de pacientes devolvió "
                "un formato inesperado."
            )

        return result

    async def search_doctors(
        self,
        name: str,
    ) -> list[dict[str, Any]]:
        result = await self.get(
            "/doctors/search",
            params={
                "name": name,
            },
        )

        if not isinstance(result, list):
            raise NestAPIError(
                "La búsqueda de médicos devolvió "
                "un formato inesperado."
            )

        return result

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
                "durationMinutes":
                    duration_minutes,
            },
        )

        if not isinstance(result, dict):
            raise NestAPIError(
                "La disponibilidad devolvió "
                "un formato inesperado."
            )

        return result

    async def create_appointment(
        self,
        body: dict[str, Any],
    ) -> dict[str, Any]:
        result = await self.post(
            "/appointments",
            body,
        )

        if not isinstance(result, dict):
            raise NestAPIError(
                "La creación de la cita devolvió "
                "un formato inesperado."
            )

        return result

    def _build_url(
        self,
        endpoint: str,
    ) -> str:
        return (
            f"{self.base_url}/"
            f"{endpoint.lstrip('/')}"
        )

    @staticmethod
    def _get_error_detail(
        response: httpx.Response,
    ) -> str:
        try:
            payload = response.json()

            if isinstance(payload, dict):
                message = payload.get(
                    "message",
                )

                if isinstance(message, list):
                    return "; ".join(
                        str(item)
                        for item in message
                    )

                if message:
                    return str(message)

            return str(payload)

        except ValueError:
            return (
                response.text
                or "Error sin detalle"
            )
