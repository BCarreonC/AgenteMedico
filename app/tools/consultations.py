from app.services.nest_api import NestAPIClient

api = NestAPIClient()


class ConsultationsTool:

    async def execute(self):

        return await api.get("/consultations")