from langchain_ollama import OllamaEmbeddings

from app.config.settings import settings


embeddings = OllamaEmbeddings(
    model=settings.OLLAMA_EMBEDDING_MODEL,
    base_url=settings.OLLAMA_BASE_URL,
)
