import base64
import io
import json

from fastapi.testclient import TestClient

from app import main as main_module
from app.extraction import groq as groq_module
from app.extraction import service as extraction_service
from app.extraction.base import VisionRequest, VisionResponse
from app.extraction.groq import GroqProvider
from app.models import (ImageObservation, ImageObservationBatch,
                        IndexedImageObservation)

client = TestClient(main_module.app)
AUTH = {"Authorization": "Bearer alpha-demo-token"}
PO = {"unit_id": "UNIT-BATCH", "po_number": "PO-BATCH",
    "line_items": [{"sku": "SKU-BATCH", "qty_ordered": 2}]}
PNG_BYTES = b"\x89PNG\r\n\x1a\nnot-a-real-image"


class RecordingProvider:
    name = "test-provider"

    def __init__(self):
        self.calls = []

    def analyze(self, request):
        self.calls.append(request)
        observations = [
            IndexedImageObservation(
                image_index=index,
                observation=ImageObservation(visible_sku_text=f"SKU-{index}"))
            for index in reversed(range(len(request.image_bytes)))
        ]
        return VisionResponse(
            parsed=ImageObservationBatch(images=observations), raw_text="",
            model_id="test-model", prompt_version=request.prompt_version,
            latency_ms=125, tokens=60)


def _prepare(monkeypatch, tmp_path):
    monkeypatch.setattr(extraction_service.CFG, "cache_dir", tmp_path)
    monkeypatch.setattr(extraction_service, "process_image", lambda raw: raw)
    monkeypatch.setattr(extraction_service, "assess_quality", lambda raw: {
        "verdict": "ACCEPTABLE", "reasons": []})
    monkeypatch.setattr(extraction_service, "decode_barcodes", lambda raw: [])


def test_observe_unit_batches_images_and_maps_by_index(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    provider = RecordingProvider()
    service = extraction_service.ExtractionService(provider)

    results = service.observe_unit([
        ("sha-1", "img_1", b"first"),
        ("sha-2", "img_2", b"second"),
    ])

    assert len(provider.calls) == 1
    assert provider.calls[0].image_bytes == [b"first", b"second"]
    assert [result.provenance.observation.visible_sku_text for result in results] == [
        "SKU-0", "SKU-1"]
    assert results[0].provenance.latency_ms == 125
    assert results[1].provenance.latency_ms == 0


def test_observe_unit_uses_cached_observations_without_another_call(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    provider = RecordingProvider()
    service = extraction_service.ExtractionService(provider)
    inputs = [("sha-1", "img_1", b"first"), ("sha-2", "img_2", b"second")]

    first = service.observe_unit(inputs)
    second = service.observe_unit(inputs)

    assert len(provider.calls) == 1
    assert [result.provenance.observation.visible_sku_text for result in second] == [
        "SKU-0", "SKU-1"]
    assert all(result.provenance.latency_ms == 0 for result in second)
    assert first[0].provenance.tokens == 60
    assert first[1].provenance.tokens == 0


def test_observe_unit_returns_image_errors_on_provider_failure(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)

    class FailedProvider:
        name = "failed-provider"

        def analyze(self, request):
            raise RuntimeError("provider unavailable")

    service = extraction_service.ExtractionService(FailedProvider())
    results = service.observe_unit([
        ("sha-1", "img_1", b"first"),
        ("sha-2", "img_2", b"second"),
    ])

    assert [result.image_id for result in results] == ["img_1", "img_2"]
    assert all(result.provenance is None for result in results)
    assert all("provider unavailable" in result.error for result in results)


def test_missing_api_key_is_captured_as_an_extraction_error(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)
    monkeypatch.setattr(extraction_service.CFG, "groq_api_key", "")
    service = extraction_service.ExtractionService(GroqProvider())

    results = service.observe_unit([("sha-1", "img_1", b"first")])

    assert results[0].provenance is None
    assert "GROQ_API_KEY missing" in results[0].error


def test_groq_provider_sends_images_and_validates_json(monkeypatch):
    monkeypatch.setattr(extraction_service.CFG, "groq_api_key", "test-key")
    provider = GroqProvider()
    response_text = json.dumps({"images": [{
        "image_index": 0,
        "observation": {"visible_sku_text": "SKU-0"},
    }]})

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "model": "test-groq-model",
                "choices": [{"message": {"content": response_text}}],
                "usage": {"total_tokens": 23},
            }

    request_details = {}

    def fake_post(url, headers, timeout, json):
        request_details.update(url=url, headers=headers, timeout=timeout, payload=json)
        return FakeResponse()

    monkeypatch.setattr(groq_module.httpx, "post", fake_post)
    result = provider._call("test-groq-model", VisionRequest(
        image_bytes=[b"jpeg-data"], prompt_text="Observe images",
        prompt_version="batch-v1", schema_model=ImageObservationBatch))

    payload = request_details["payload"]
    parts = payload["messages"][0]["content"]
    assert request_details["url"] == (
        "https://api.groq.com/openai/v1/chat/completions")
    assert request_details["headers"]["Authorization"] == "Bearer test-key"
    assert payload["response_format"] == {"type": "json_object"}
    assert parts[1]["image_url"]["url"] == (
        "data:image/jpeg;base64," + base64.b64encode(b"jpeg-data").decode("ascii"))
    assert "Return JSON matching this schema" in parts[-1]["text"]
    assert result.parsed.images[0].observation.visible_sku_text == "SKU-0"
    assert result.model_id == "test-groq-model"
    assert result.tokens == 23


def test_failed_batch_is_saved_for_human_review(monkeypatch, tmp_path):
    _prepare(monkeypatch, tmp_path)

    class FailedProvider:
        name = "failed-provider"

        def analyze(self, request):
            raise RuntimeError("provider unavailable")

    monkeypatch.setattr(main_module, "GroqProvider", FailedProvider)
    created = client.post("/api/records", json=PO, headers=AUTH)
    assert created.status_code == 200
    record_id = created.json()["record_id"]
    uploaded = client.post(
        f"/api/records/{record_id}/images",
        files={"files": ("carton.png", io.BytesIO(PNG_BYTES), "image/png")},
        headers=AUTH)
    assert uploaded.status_code == 200

    inspected = client.post(f"/api/records/{record_id}/inspect", headers=AUTH)

    assert inspected.status_code == 200
    assert inspected.json()["inspection_status"] == "PENDING_REVIEW"
    assert inspected.json()["outcome"]["decision"] == "UNCERTAIN"
    assert "provider unavailable" in inspected.json()["images"][0]["extraction_error"]