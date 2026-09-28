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

# Runtime data location can be redirected (tests, deployment) without touching .env
DATA_DIR = Path(os.environ.get("RCV_DATA_DIR", str(ROOT_DIR / "data")))

class Config:
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")
    gemini_model: str = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")
    gemini_fallback_models: list = [m.strip() for m in os.environ.get(
        "GEMINI_FALLBACK_MODELS", "").split(",") if m.strip()]
    db_path: Path = DATA_DIR / "app.db"
    image_dir: Path = DATA_DIR / "images"
    cache_dir: Path = Path(os.environ.get("RCV_CACHE_DIR", str(ROOT_DIR / ".cache"))) / "extraction"
    prompts_dir: Path = BACKEND_DIR / "prompts"
    max_image_bytes: int = 10 * 1024 * 1024
    max_images_per_record: int = 8
    agent_version: str = "0.2.0-contract"
    schema_version: str = "1.1.0"

# Demo-grade org tokens (static; documented as such — production would use real auth)
ALPHA_TOKEN = os.environ.get("ORG_ALPHA_TOKEN", "alpha-demo-token")
BRAVO_TOKEN = os.environ.get("ORG_BRAVO_TOKEN", "bravo-demo-token")
ORG_TOKENS = {ALPHA_TOKEN: "org_demo_alpha", BRAVO_TOKEN: "org_demo_bravo"}

CFG = Config()