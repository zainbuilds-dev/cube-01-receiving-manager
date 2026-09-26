import io
import time

from google import genai
from google.genai import types
from PIL import Image
from pydantic import ValidationError

from ..config import CFG
from .base import VisionProvider, VisionRequest, VisionResponse

RETRYABLE_STATUS = ("429", "RESOURCE_EXHAUSTED", "500", "503", "UNAVAILABLE", "OVERLOADED")
BACKOFF_S = (2, 5)

class GeminiProvider(VisionProvider):
    name = "gemini"

    def __init__(self):
        if not CFG.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY missing in .env")
        self.client = genai.Client(api_key=CFG.gemini_api_key)
        self.model = CFG.gemini_model

    def analyze(self, req: VisionRequest) -> VisionResponse:
        img = Image.open(io.BytesIO(req.image_bytes))
        last = None
        for attempt in range(len(BACKOFF_S) + 1):
            t0 = time.time()
            try:
                resp = self.client.models.generate_content(
                    model=self.model,
                    contents=[img, req.prompt_text],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=req.schema_model,
                    ),
                )
                parsed = req.schema_model.model_validate_json(resp.text)
                usage = getattr(resp, "usage_metadata", None)
                tokens = int(getattr(usage, "total_token_count", 0) or 0)
                return VisionResponse(
                    parsed=parsed, raw_text=resp.text, model_id=self.model,
                    prompt_version=req.prompt_version,
                    latency_ms=int((time.time() - t0) * 1000), tokens=tokens)
            except ValidationError as e:
                last = e  # schema violation: retry, model may self-correct
            except Exception as e:
                last = e
                if not any(s in str(e) for s in RETRYABLE_STATUS):
                    raise
            if attempt < len(BACKOFF_S):
                time.sleep(BACKOFF_S[attempt])
        raise last