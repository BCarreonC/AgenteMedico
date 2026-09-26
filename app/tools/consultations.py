from app.services.nest_api import nest_api as api

class ConsultationsTool:

    async def execute(self):

        return await api.get("/consultations")