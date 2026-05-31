from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="v2/.env", extra="ignore")

    bot_token: str = ""
    operator_chat_id: int = 0
    admin_api_base_url: str = "http://admin-api:8000"


settings = Settings()
