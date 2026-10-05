import io

import qrcode
from PIL import Image

from app.extraction.barcode import barcode_available, decode_barcodes


def _qr_jpeg(payload: str, box_size: int = 10) -> bytes:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=box_size, border=4)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").get_image().convert("RGB")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=92)
    return buf.getvalue()


def _plain_jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (640, 480), (128, 128, 128)).save(buf, "JPEG", quality=90)
    return buf.getvalue()


def test_barcode_available():
    assert barcode_available() is True


def test_decode_matching_payload():
    assert decode_barcodes(_qr_jpeg("SKU-BOTTLE-750")) == ["SKU-BOTTLE-750"]


def test_decode_second_payload():
    assert decode_barcodes(_qr_jpeg("SKU-LEASH-6FT")) == ["SKU-LEASH-6FT"]


def test_no_qr_returns_empty():
    assert decode_barcodes(_plain_jpeg()) == []


def test_garbage_bytes_return_empty():
    assert decode_barcodes(b"not an image at all") == []