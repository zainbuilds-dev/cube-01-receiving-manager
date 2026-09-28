"""Print quality-gate metrics for photo(s) so thresholds in
backend/app/quality.py can be validated against real photos.

Usage:  venv\\Scripts\\python.exe scripts\\quality_probe.py photo1.jpg blurry.jpg
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.quality import assess_quality          # noqa: E402
from app.extraction.service import process_image  # noqa: E402

for p in sys.argv[1:]:
    q = assess_quality(process_image(Path(p).read_bytes()))
    print(f"{p}: {q}")