from app.rag.retriever import retriever

class RagTool:

    async def execute(self,query):

        docs=retriever.invoke(query)

        context = "\n\n".join(doc.page_content for doc in docs)

        return context