import dotenv
import os

# Load environment variables from .env file
dotenv.load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "gateway")
POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

POSTGRES_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

PROVIDER = os.getenv("PROVIDER", "")
PROVIDER_API_KEY = os.getenv("PROVIDER_API_KEY", "")
FREE_PROVIDER_API_KEY = os.getenv("FREE_PROVIDER_API_KEY", "")
PROVIDER_API_BASE = os.getenv("PROVIDER_API_BASE", "")
PROVIDER_MODEL = os.getenv("PROVIDER_MODEL", "")
PROVIDER_VISION_MODEL = os.getenv("PROVIDER_VISION_MODEL", "")
PROVIDER_VISION_TOOL_MODEL = os.getenv("PROVIDER_VISION_TOOL_MODEL", "")
PROVIDER_GROUNDING_MODEL = os.getenv("PROVIDER_GROUNDING_MODEL", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

UI_ERROR_PLANNING = os.getenv("UI_ERROR_PLANNING", "false").lower() == "true"
