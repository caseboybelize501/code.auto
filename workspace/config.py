from pydantic import BaseModel
from typing import Optional

class Settings(BaseModel):
    app_name: str = "Auto-Generated API"
    debug: bool = True
    database_url: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
