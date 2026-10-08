from pathlib import Path

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
  database_url: str

  model_config = SettingsConfigDict(env_file=BASE_DIR / '.env')

@lru_cache
def get_settings() -> Settings:
  return Settings()
