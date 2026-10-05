import hashlib
import io
import json
from dataclasses import dataclass
from typing import Optional

from PIL import Image, ImageOps

from ..config import CFG
from ..models import ImageObservation, ImageObservationBatch, ObsProvenance
from ..quality import assess_quality
from .base import VisionProvider, VisionRequest
from .barcode import decode_barcodes

PROMPT_FILE = "observe_carton.batch.v1.txt"
PROMPT_VERSION = "observe_carton_batch@v1"

@dataclass
class ExtractionResult:
    image_id: str
    provenance: Optional[ObsProvenance] = None
    model_id: Optional[str] = None
    error: Optional[str] = None

def load_prompt() -> str:
    return (CFG.prompts_dir / PROMPT_FILE).read_text(encoding="utf-8")

def process_image(raw: bytes) -> bytes:
    """EXIF-rotate (phone photos!), downscale to <=1280px, re-encode JPEG."""
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
    if max(img.size) > 1280:
        img.thumbnail((1280, 1280))
    out = io.BytesIO()
    img.save(out, "JPEG", quality=85)
    return out.getvalue()

class ExtractionService:
    """Prepare every photo in a unit, then use at most one vision call."""

    def __init__(self, provider: VisionProvider):
        self.provider = provider
        CFG.cache_dir.mkdir(parents=True, exist_ok=True)

    def observe_unit(self, images: list[tuple[str, str, bytes]]) -> list[ExtractionResult]:
        results: list[Optional[ExtractionResult]] = [None] * len(images)
        pending = []

        for position, (original_sha, image_id, raw) in enumerate(images):
            try:
                processed = process_image(raw)
                quality = assess_quality(processed)
                barcodes = decode_barcodes(processed)
            except Exception as error:
                results[position] = ExtractionResult(
                    image_id=image_id,
                    error=f"{type(error).__name__}: {str(error)[:160]}")
                continue

            if quality["verdict"] == "REJECTED":
                results[position] = ExtractionResult(
                    image_id=image_id,
                    provenance=ObsProvenance(
                        image_id=image_id, sha256=original_sha,
                        observation=ImageObservation(), barcodes=barcodes,
                        quality=quality))
                continue

            key = hashlib.sha256(
                f"{self.provider.name}|{CFG.groq_model}|{PROMPT_VERSION}|"
                f"{hashlib.sha256(processed).hexdigest()}".encode()
            ).hexdigest()[:24]
            cache_file = CFG.cache_dir / f"{key}.json"
            cached_observation = None
            cached_model_id = None
            cached_tokens = 0
            if cache_file.exists():
                try:
                    cached = json.loads(cache_file.read_text(encoding="utf-8"))
                    cached_observation = ImageObservation(**cached["parsed"])
                    cached_model_id = cached["model_id"]
                    cached_tokens = cached.get("tokens", 0)
                except Exception:
                    cached_observation = None

            if cached_observation is not None:
                results[position] = ExtractionResult(
                    image_id=image_id,
                    provenance=ObsProvenance(
                        image_id=image_id, sha256=original_sha,
                        observation=cached_observation,
                        barcodes=barcodes, quality=quality,
                        tokens=cached_tokens),
                    model_id=cached_model_id)
                continue

            pending.append({
                "position": position, "sha": original_sha, "image_id": image_id,
                "processed": processed, "barcodes": barcodes,
                "quality": quality, "cache_file": cache_file,
            })

        if pending:
            try:
                CFG.cache_dir.mkdir(parents=True, exist_ok=True)
            except OSError:
                pass
            try:
                response = self.provider.analyze(VisionRequest(
                    image_bytes=[item["processed"] for item in pending],
                    prompt_text=load_prompt(), prompt_version=PROMPT_VERSION,
                    schema_model=ImageObservationBatch))
                by_index = {item.image_index: item.observation
                            for item in response.parsed.images}
                if (len(response.parsed.images) != len(pending)
                    or set(by_index) != set(range(len(pending)))):
                    raise ValueError("Batch response did not contain exactly one observation per image")

                for batch_index, item in enumerate(pending):
                    observation = by_index[batch_index]
                    try:
                        item["cache_file"].write_text(json.dumps({
                            "parsed": observation.model_dump(),
                            "model_id": response.model_id,
                            "tokens": response.tokens if batch_index == 0 else 0,
                        }), encoding="utf-8")
                    except OSError:
                        pass
                    results[item["position"]] = ExtractionResult(
                        image_id=item["image_id"],
                        provenance=ObsProvenance(
                            image_id=item["image_id"], sha256=item["sha"],
                            observation=observation, barcodes=item["barcodes"],
                            quality=item["quality"],
                            latency_ms=response.latency_ms if batch_index == 0 else 0,
                            tokens=response.tokens if batch_index == 0 else 0),
                        model_id=response.model_id)
            except Exception as error:
                detail = f"{type(error).__name__}: {str(error)[:160]}"
                for item in pending:
                    results[item["position"]] = ExtractionResult(
                        image_id=item["image_id"], error=detail)

        return [result for result in results if result is not None]