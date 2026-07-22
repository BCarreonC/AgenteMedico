from app.services.nest_api import NestAPIClient

api = NestAPIClient()


class NotificationsTool:

    async def execute(self):

        return await api.get("/notifications")