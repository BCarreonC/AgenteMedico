from app.services.nest_api import NestAPIClient


api = NestAPIClient()

class PatientsTool:

    async def execute(self, data):

        return await api.get("/patients")
    
