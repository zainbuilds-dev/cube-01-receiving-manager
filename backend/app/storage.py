import hashlib

from .config import CFG

def sniff_format(b: bytes):
    if b[:3] == b"\xff\xd8\xff":
        return "jpg"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "webp"
    return None

def store_image(raw: bytes):
    """Validate by magic bytes (never trust extensions), store content-addressed."""
    ext = sniff_format(raw)
    if not ext:
        raise ValueError("unsupported image format (JPEG/PNG/WebP only)")
    sha = hashlib.sha256(raw).hexdigest()
    CFG.image_dir.mkdir(parents=True, exist_ok=True)
    path = CFG.image_dir / f"{sha}.{ext}"
    if not path.exists():
        path.write_bytes(raw)
    return sha, ext, len(raw)