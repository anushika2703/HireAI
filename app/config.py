import os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE / "data"))
DB_PATH = DATA_DIR / "app.db"
SEED_DIR = BASE / "seed"

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
USE_LLM = os.getenv("USE_LLM", "1") == "1"

# Final score = weighted blend of three 0-1 components.
WEIGHTS = {"skills": 0.50, "relevance": 0.35, "experience": 0.15}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
