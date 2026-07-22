from app.services.nest_api import NestAPIClient

api = NestAPIClient()


class AppointmentsTool:

    async def execute(self):

        return await api.get("/appointments")