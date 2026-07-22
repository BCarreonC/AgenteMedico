import httpx

from app.config.settings import settings


class NestAPIClient:

    def __init__(self):

        self.base = settings.NEST_API

    async def get(self, endpoint: str):

        async with httpx.AsyncClient() as client:

            response = await client.get(
                f"{self.base}{endpoint}"
            )

            response.raise_for_status()

            return response.json()

    async def post(self, endpoint: str, body: dict):

        async with httpx.AsyncClient() as client:

            response = await client.post(
                f"{self.base}{endpoint}",
                json=body
            )

            response.raise_for_status()

            return response.json()