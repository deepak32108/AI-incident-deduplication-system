import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.85))
    TIME_WINDOW_MINUTES = int(os.getenv("TIME_WINDOW_MINUTES", 60))
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vector_store.json")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/incidents.db")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

config = Config()