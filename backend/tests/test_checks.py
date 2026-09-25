from app.checks import damage, quantity, sku, variant
from app.models import (DamageObs, CheckContext, ImageObservation, ObsProvenance, POLineItem)

def obs(**kw):
    base = dict(visible_sku_text=None, visible_product_text=None, printed_quantity=None,
                visible_unit_count=None, count_confidence=None, full_contents_visible=False,
                cartons_visible=1, dominant_product_color=None, color_reliability="good",
                label_variant_text=None, damages=[], quality_issues=[], notes=None)
    base.update(kw)
    return ImageObservation(**base)

def ctx(obs_list, **po_kw):
    kw = dict(sku="BLUE-BOTTLE-001", expected_qty=24, variant="Blue")
    kw.update(po_kw)          # allow tests to override any PO field
    po = POLineItem(**kw)
    provs = [ObsProvenance(image_id=f"img_{i+1}", sha256=f"sha{i}", observation=o)
             for i, o in enumerate(obs_list)]
    return CheckContext(po=po, observations=provs, model_version="gemini:test|prompt:v1")
# ---- SKU ----
def test_sku_pass():
    assert sku.run(ctx([obs(visible_sku_text="BLUE-BOTTLE-001")])).verdict == "PASS"

def test_sku_fail():
    assert sku.run(ctx([obs(visible_sku_text="RED-CAN-002")])).verdict == "FAIL"

def test_sku_uncertain():
    r = sku.run(ctx([obs(), obs()]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "INSUFFICIENT_EVIDENCE"

# ---- quantity ----
def test_qty_pass():
    assert quantity.run(ctx([obs(visible_unit_count=24, count_confidence=0.9,
                                 full_contents_visible=True)])).verdict == "PASS"

def test_qty_short_fail():
    r = quantity.run(ctx([obs(visible_unit_count=22, count_confidence=0.9,
                              full_contents_visible=True)]))
    assert r.verdict == "FAIL" and "22" in r.detail

def test_qty_overage_partial_fail():
    r = quantity.run(ctx([obs(visible_unit_count=27, count_confidence=0.5,
                              full_contents_visible=False)]))
    assert r.verdict == "FAIL" and "overage" in r.detail

def test_qty_occlusion_uncertain():
    r = quantity.run(ctx([obs(visible_unit_count=18, count_confidence=0.6,
                              full_contents_visible=False)]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "OCCLUSION"

def test_qty_printed_only_uncertain():
    assert quantity.run(ctx([obs(printed_quantity=24)])).verdict == "UNCERTAIN"

def test_qty_printed_conflict_uncertain():
    r = quantity.run(ctx([obs(printed_quantity=12)]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "CONFLICTING_EVIDENCE"

# ---- variant ----
def test_variant_label_pass():
    assert variant.run(ctx([obs(label_variant_text="Blue")])).verdict == "PASS"

def test_variant_label_fail():
    assert variant.run(ctx([obs(label_variant_text="Red")])).verdict == "FAIL"

def test_variant_color_conflict():
    r = variant.run(ctx([obs(dominant_product_color="blue"),
                         obs(dominant_product_color="red")]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "CONFLICTING_EVIDENCE"

def test_variant_poor_lighting():
    r = variant.run(ctx([obs(dominant_product_color="blue", color_reliability="poor")]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "LOW_IMAGE_QUALITY"

def test_variant_not_applicable():
    assert variant.run(ctx([obs()], variant=None)).verdict == "NOT_APPLICABLE"

# ---- damage ----
def test_damage_fail():
    r = damage.run(ctx([obs(damages=[DamageObs(damage_type="crushing",
                                               location="upper-right corner",
                                               severity="major", confidence=0.9)])]))
    assert r.verdict == "FAIL"

def test_damage_pass():
    r = damage.run(ctx([obs(), obs()]))
    assert r.verdict == "PASS" and r.confidence == 0.7