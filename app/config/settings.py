from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    #API
    NEST_API: str = "http://127.0.0.1:3000/api"

    #APP
    APP_TIMEZONE: str = "America/Mexico_City"

    #OLLAMA
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen3:1.7b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    OLLAMA_KEEP_ALIVE: str = "30m"
    OLLAMA_NUM_PREDICT: int = 128

    #PLANNER
    PLANNER_HISTORY_TURNS: int = 3

    #LOGGER
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()