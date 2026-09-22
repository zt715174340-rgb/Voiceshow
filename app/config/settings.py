"""Environment-backed settings. Pseudocode only."""

class Settings:
    llm_api_key: str
    llm_model: str
    database_url: str
    redis_url: str
    vector_database_url: str
    jwt_secret: str


settings = load_settings_from_environment()
