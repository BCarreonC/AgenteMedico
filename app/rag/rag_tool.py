import time

from app.rag.retriever import retriever
from app.utils.logger import (
    elapsed_ms,
    get_logger,
    get_request_id,
)


logger = get_logger("rag_tool")


class RagTool:
    async def execute(self, query):
        started_at = time.perf_counter()
        documents_count: int | None = None
        status = "error"

        try:
            docs = retriever.invoke(query)

            documents_count = len(docs)

            context = "\n\n".join(
                doc.page_content
                for doc in docs
            )

            status = "ok"

            return context

        finally:
            logger.info(
                "[%s] [PERF] rag.retrieve elapsed_ms=%.2f "
                "documents=%s status=%s",
                get_request_id(),
                elapsed_ms(started_at),
                documents_count,
                status,
            )