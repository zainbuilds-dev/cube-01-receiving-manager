import io
import time

from google import genai
from google.genai import types
from PIL import Image
from pydantic import ValidationError

from ..config import CFG
from .base import VisionProvider, VisionRequest, VisionResponse

RETRYABLE_STATUS = ("429", "RESOURCE_EXHAUSTED", "500", "503", "UNAVAILABLE", "OVERLOADED")

class GeminiProvider(VisionProvider):
    """Tries the primary model, then configured fallbacks. A single
    overloaded/retired model never kills an inspection: either a fallback
    succeeds, or the fail-open path in main.py preserves the capture."""
    name = "gemini"

    def __init__(self):
        if not CFG.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY missing in .env")
        self.client = genai.Client(api_key=CFG.gemini_api_key)
        self.models = [CFG.gemini_model] + CFG.gemini_fallback_models

    def _call(self, model: str, req: VisionRequest) -> VisionResponse:
        img = Image.open(io.BytesIO(req.image_bytes))
        t0 = time.time()
        resp = self.client.models.generate_content(
            model=model,
            contents=[img, req.prompt_text],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=req.schema_model,
            ),
        )
        parsed = req.schema_model.model_validate_json(resp.text)
        usage = getattr(resp, "usage_metadata", None)
        tokens = int(getattr(usage, "total_token_count", 0) or 0)
        return VisionResponse(parsed=parsed, raw_text=resp.text, model_id=model,
                              prompt_version=req.prompt_version,
                              latency_ms=int((time.time() - t0) * 1000), tokens=tokens)

    def analyze(self, req: VisionRequest) -> VisionResponse:
        last = None
        for model in self.models:
            for attempt in range(2):            # 2 tries per model, 2s apart
                try:
                    return self._call(model, req)
                except ValidationError as e:
                    last = e                    # schema violation: retry same model
                except Exception as e:
                    last = e
                    if not any(s in str(e) for s in RETRYABLE_STATUS):
                        raise                   # non-retryable (bad key, 404): fail fast
                time.sleep(2)
            # -> next model in the chain
        raise last