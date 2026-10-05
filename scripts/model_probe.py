"""Probe configured Groq vision models. Usage:
   venv\\Scripts\\python.exe scripts\\model_probe.py
"""
import io
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.config import CFG
from app.extraction.base import VisionRequest
from app.extraction.groq import GroqProvider
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel

class Obs(BaseModel):
    dominant_color: str
    visible_text: str | None

CANDIDATES = [CFG.groq_model]

img = Image.new("RGB", (640, 480), (230, 230, 230))
d = ImageDraw.Draw(img)
d.rectangle([120, 120, 520, 360], fill=(40, 70, 200))
try: font = ImageFont.load_default(size=64)
except TypeError: font = ImageFont.load_default()
d.text((280, 200), "24", fill=(255, 255, 255), font=font)

image_bytes = io.BytesIO()
img.save(image_bytes, format="JPEG")
request = VisionRequest(
    image_bytes=[image_bytes.getvalue()],
    prompt_text="Report the dominant color and any visible text.",
    prompt_version="model-probe",
    schema_model=Obs,
)
print("Probing configured Groq models...\\n")
for m in CANDIDATES:
    try:
        t0 = time.time()
        CFG.groq_model = m
        CFG.groq_fallback_models = []
        r = GroqProvider().analyze(request)
        p = r.parsed
        ok = "blue" in p.dominant_color.lower() and p.visible_text and "24" in p.visible_text
        print(f"  {'OK  ' if ok else 'WEAK'} {m}  ({time.time()-t0:.1f}s)  "
              f"color={p.dominant_color!r} text={p.visible_text!r}")
    except Exception as e:
        print(f"  FAIL {m}  {type(e).__name__}: {str(e)[:90]}")
        time.sleep(1)

print("\\nSet GROQ_MODEL and GROQ_FALLBACK_MODELS in the environment to select working models.")