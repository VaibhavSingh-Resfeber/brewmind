import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(
            f"Missing required environment variable: {name}\n"
            f"Add it to your .env file: {name}=<your_value>"
        )
    return value


class Settings:
    DATABASE_URL: str = _require("DATABASE_URL")
    ANTHROPIC_API_KEY: str = _require("ANTHROPIC_API_KEY")
    APP_ENV: str = os.getenv("APP_ENV", "development")


settings = Settings()
