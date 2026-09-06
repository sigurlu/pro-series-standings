from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/standings"
    frontend_origin: str = "http://localhost:3000"
    scrape_token: str = "dev-scrape-token"


settings = Settings()
