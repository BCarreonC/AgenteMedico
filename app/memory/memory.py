
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.config.settings import settings
from app.utils.logger import get_logger


logger = get_logger("memory")


@asynccontextmanager
async def open_checkpointer() -> AsyncIterator[AsyncSqliteSaver]:
    """
    Abre un checkpointer SQLite persistente.

    La conexión permanece activa durante el ciclo
    de vida de FastAPI y se cierra al apagarlo.
    """

    database_path = Path(
        settings.CHECKPOINT_DB_PATH
    ).expanduser()

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger.info(
        "[MEMORY] Abriendo checkpoint database=%s",
        database_path,
    )

    async with AsyncSqliteSaver.from_conn_string(
        str(database_path)
    ) as checkpointer:

        await checkpointer.setup()

        logger.info(
            "[MEMORY] Checkpointer persistente preparado"
        )

        yield checkpointer

    logger.info(
        "[MEMORY] Conexión SQLite cerrada"
    )
