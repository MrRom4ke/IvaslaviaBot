from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="v2/.env", extra="ignore")

    app_name: str = "Ivaslavia Admin API"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    secret_key: str = "changeme-secret-key-for-jwt"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    bot_token: str = ""  # Telegram Bot Token для отправки уведомлений


settings = Settings()
