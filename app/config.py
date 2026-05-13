from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM backend — any OpenAI-compatible endpoint
    # Defaults to Ollama running locally (no key required)
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"      # Ollama ignores this; set a real key for hosted providers
    llm_model: str = "llama3.1:8b"  # swap to llama3.3:70b, qwen2.5:14b, etc.

    newsapi_key: str = ""
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
