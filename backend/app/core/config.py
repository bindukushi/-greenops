"""
Centralized application configuration.

Reads from environment variables (see .env.example). All values have safe
defaults so the project can be started immediately for a demo.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Mongo
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "greenai"

    # Auth
    jwt_secret_key: str = "dev_secret_change_me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    # LLM (optional - AI assistant works without these via templates/rules)
    openai_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""

    # Carbon engine
    default_carbon_factor: float = 0.82  # kg CO2 per kWh (grid average, configurable per region)

    # App
    app_name: str = "GreenAI"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]


settings = Settings()
