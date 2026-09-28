"""Find a vision model that works RIGHT NOW. Usage:
   venv\\Scripts\\python.exe scripts\\model_probe.py
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.config import CFG
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel

class Obs(BaseModel):
    dominant_color: str
    visible_text: str | None

CANDIDATES = [CFG.gemini_model,
    "gemini-flash-latest", "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash",
    "gemini-3.7-flash", "gemini-3.8-flash", "gemini-2.5-flash-lite"]

img = Image.new("RGB", (640, 480), (230, 230, 230))
d = ImageDraw.Draw(img)
d.rectangle([120, 120, 520, 360], fill=(40, 70, 200))
try: font = ImageFont.load_default(size=64)
except TypeError: font = ImageFont.load_default()
d.text((280, 200), "24", fill=(255, 255, 255), font=font)

client = genai.Client(api_key=CFG.gemini_api_key)
print("Probing candidates (SDK retries internally on 503 — may take a few min)...\n")
winners = []
for m in CANDIDATES:
    try:
        t0 = time.time()
        r = client.models.generate_content(
            model=m, contents=[img, "Report the dominant color and any visible text."],
            config=types.GenerateContentConfig(response_mime_type="application/json",
                                               response_schema=Obs))
        p = Obs.model_validate_json(r.text)
        ok = "blue" in p.dominant_color.lower() and p.visible_text and "24" in p.visible_text
        print(f"  {'OK  ' if ok else 'WEAK'} {m}  ({time.time()-t0:.1f}s)  "
              f"color={p.dominant_color!r} text={p.visible_text!r}")
        if ok: winners.append(m)
    except Exception as e:
        print(f"  FAIL {m}  {type(e).__name__}: {str(e)[:90]}")
        time.sleep(1)

print()
if winners:
    print(f"PRIMARY -> GEMINI_MODEL={winners[0]}")
    print(f"FALLBACKS -> GEMINI_FALLBACK_MODELS={','.join(winners[1:3])}")
else:
    print("ALL FAILED — paste this output back.")