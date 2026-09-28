"""Deterministic barcode/QR tier (Tier-1 evidence) via pyzbar.
Optional dependency: if unavailable (missing package or system zbar lib),
this tier degrades gracefully — checks fall back to label text and never crash."""
import io
import logging

log = logging.getLogger("rcv.barcode")

try:
    from PIL import Image
    from pyzbar.pyzbar import decode as _pyzbar_decode
    _AVAILABLE = True
except Exception as e:  # ImportError or missing zbar shared library
    _AVAILABLE = False
    log.warning("pyzbar unavailable (%s); barcode tier disabled", e)

def barcode_available() -> bool:
    return _AVAILABLE

def decode_barcodes(jpeg_bytes: bytes) -> list:
    """Distinct decoded barcode/QR payloads (local, free, deterministic)."""
    if not _AVAILABLE:
        return []
    try:
        out = []
        for r in _pyzbar_decode(Image.open(io.BytesIO(jpeg_bytes))):
            try:
                text = r.data.decode("utf-8").strip()
            except Exception:
                continue
            if text and text not in out:
                out.append(text)
        return out
    except Exception as e:
        log.warning("barcode decode failed: %s", e)
        return []