import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent

def _load_env():
    env = ROOT_DIR / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_env()

class Config:
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")
    gemini_model: str = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")
    db_path: Path = ROOT_DIR / "data" / "app.db"
    image_dir: Path = ROOT_DIR / "data" / "images"
    cache_dir: Path = ROOT_DIR / ".cache" / "extraction"
    prompts_dir: Path = BACKEND_DIR / "prompts"
    max_image_bytes: int = 10 * 1024 * 1024
    max_images_per_record: int = 8
    agent_version: str = "0.1.0-mvp"
    schema_version: str = "1.0.0"
    org_id: str = "org_demo"
    client_id: str = "client_demo"

CFG = Config()