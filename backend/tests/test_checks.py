from app.checks import (carton_count, carton_damage, colour, missing_components,
                        other_quality, quantity, sku, unit_damage, units_per_carton,
                        variant)
from app.models import (CheckContext, DamageObs, ImageObservation, ObsProvenance,
                        POLineItem)

def obs(**kw):
    base = dict(visible_sku_text=None, visible_product_text=None, printed_quantity=None,
                visible_unit_count=None, count_confidence=None, full_contents_visible=False,
                cartons_visible=1, dominant_product_color=None, color_reliability="good",
                label_colour_text=None, label_variant_text=None, visible_components=None,
                contents_open_for_inspection=False, damages=[], quality_issues=[], notes=None)
    base.update(kw)
    return ImageObservation(**base)

def ctx(obs_list, **po_kw):
    kw = dict(sku="SKU-BOTTLE-750", qty_ordered=24, spec_colour="black",
              spec_variant="750ml", spec_components=["bottle", "lid"],
              cartons_ordered=2, units_per_carton_ordered=12)
    kw.update(po_kw)
    po = POLineItem(**kw)
    provs = [ObsProvenance(image_id=f"img_{i+1}", sha256=f"sha{i}", observation=o)
             for i, o in enumerate(obs_list)]
    return CheckContext(po=po, observations=provs, model_version="gemini:test|prompt:v2")

def ctx_barcodes(codes, **po_kw):
    kw = dict(sku="SKU-BOTTLE-750", qty_ordered=24)
    kw.update(po_kw)
    po = POLineItem(**kw)
    provs = [ObsProvenance(image_id="img_1", sha256="sha0", observation=obs(),
                           barcodes=codes)]
    return CheckContext(po=po, observations=provs, model_version="gemini:test|prompt:v2")

def dmg(target="carton", dtype="crushing", conf=0.9):
    return DamageObs(damage_type=dtype, target=target, location="upper corner",
                     severity="major", confidence=conf)

# ---- SKU (label tier) ----
def test_sku_pass():
    assert sku.run(ctx([obs(visible_sku_text="SKU-BOTTLE-750")])).verdict == "PASS"

def test_sku_fail():
    assert sku.run(ctx([obs(visible_sku_text="SKU-LEASH-6FT")])).verdict == "FAIL"

def test_sku_uncertain():
    r = sku.run(ctx([obs(), obs()]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "INSUFFICIENT_EVIDENCE"

# ---- SKU (barcode tier, deterministic) ----
def test_sku_barcode_pass():
    r = sku.run(ctx_barcodes(["SKU-BOTTLE-750"]))
    assert r.verdict == "PASS" and r.confidence == 0.95
    assert r.evidence[0].type == "barcode"

def test_sku_barcode_wrong_sku_fail():
    r = sku.run(ctx_barcodes(["SKU-LEASH-6FT"]))
    assert r.verdict == "FAIL" and r.confidence == 0.9

def test_sku_barcode_upc_ignored():
    # A numeric UPC that doesn't match is NOT evidence of a wrong SKU.
    r = sku.run(ctx_barcodes(["0123456789012"]))
    assert r.verdict == "UNCERTAIN"

# ---- colour ----
def test_colour_label_pass():
    assert colour.run(ctx([obs(label_colour_text="Black")])).verdict == "PASS"

def test_colour_label_fail():
    assert colour.run(ctx([obs(label_colour_text="Red")])).verdict == "FAIL"

def test_colour_visual_pass():
    assert colour.run(ctx([obs(dominant_product_color="black")])).verdict == "PASS"

def test_colour_visual_conflict():
    r = colour.run(ctx([obs(dominant_product_color="black"),
                        obs(dominant_product_color="white")]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "CONFLICTING_EVIDENCE"

def test_colour_poor_lighting():
    r = colour.run(ctx([obs(dominant_product_color="black", color_reliability="poor")]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "LOW_IMAGE_QUALITY"

def test_colour_not_applicable():
    assert colour.run(ctx([obs()], spec_colour=None)).verdict == "NOT_APPLICABLE"
    assert colour.run(ctx([obs()], spec_colour="n/a")).verdict == "NOT_APPLICABLE"

# ---- variant ----
def test_variant_label_pass():
    assert variant.run(ctx([obs(label_variant_text="750ml")])).verdict == "PASS"

def test_variant_label_fail():
    assert variant.run(ctx([obs(label_variant_text="1L")])).verdict == "FAIL"

def test_variant_uncertain():
    r = variant.run(ctx([obs()]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "INSUFFICIENT_EVIDENCE"

def test_variant_not_applicable():
    assert variant.run(ctx([obs()], spec_variant=None)).verdict == "NOT_APPLICABLE"

# ---- quantity ----
def test_qty_pass():
    r = quantity.run(ctx([obs(visible_unit_count=24, count_confidence=0.9,
                              full_contents_visible=True)]))
    assert r.verdict == "PASS" and r.summary_value == "24"

def test_qty_short_fail():
    r = quantity.run(ctx([obs(visible_unit_count=22, count_confidence=0.9,
                              full_contents_visible=True)]))
    assert r.verdict == "FAIL" and r.summary_value == "22" and "22" in r.detail

def test_qty_overage_partial_fail():
    r = quantity.run(ctx([obs(visible_unit_count=27, count_confidence=0.5,
                              full_contents_visible=False)]))
    assert r.verdict == "FAIL" and "overage" in r.detail

def test_qty_occlusion_uncertain():
    r = quantity.run(ctx([obs(visible_unit_count=18, count_confidence=0.6,
                              full_contents_visible=False)]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "OCCLUSION"

def test_qty_printed_only_uncertain():
    r = quantity.run(ctx([obs(printed_quantity=24)]))
    assert r.verdict == "UNCERTAIN" and r.summary_value == "uncertain"

def test_qty_printed_conflict_uncertain():
    r = quantity.run(ctx([obs(printed_quantity=12)]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "CONFLICTING_EVIDENCE"

def test_qty_no_evidence_uncertain():
    r = quantity.run(ctx([obs(), obs()]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "INSUFFICIENT_EVIDENCE"

# ---- carton count ----
def test_carton_count_pass():
    r = carton_count.run(ctx([obs(cartons_visible=2)]))
    assert r.verdict == "PASS" and r.summary_value == "2"

def test_carton_count_overage_fail():
    assert carton_count.run(ctx([obs(cartons_visible=3)])).verdict == "FAIL"

def test_carton_count_fewer_uncertain():
    r = carton_count.run(ctx([obs(cartons_visible=1)]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "OCCLUSION"

def test_carton_count_none_visible_uncertain():
    r = carton_count.run(ctx([obs(cartons_visible=0)]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "INSUFFICIENT_EVIDENCE"

def test_carton_count_not_applicable():
    assert carton_count.run(ctx([obs()], cartons_ordered=None)).verdict == "NOT_APPLICABLE"

# ---- carton damage ----
def test_carton_damage_fail():
    r = carton_damage.run(ctx([obs(damages=[dmg(target="carton")])]))
    assert r.verdict == "FAIL" and r.summary_value == "crushing"

def test_carton_damage_pass():
    r = carton_damage.run(ctx([obs(), obs()]))
    assert r.verdict == "PASS" and r.summary_value == "none"

def test_carton_damage_ignores_unit_damage():
    r = carton_damage.run(ctx([obs(damages=[dmg(target="unit")])]))
    assert r.verdict == "PASS"

# ---- unit damage ----
def test_unit_damage_fail():
    r = unit_damage.run(ctx([obs(visible_unit_count=6,
                                 damages=[dmg(target="unit", dtype="dent")])]))
    assert r.verdict == "FAIL" and r.summary_value == "dent"

def test_unit_damage_not_visible_uncertain():
    r = unit_damage.run(ctx([obs()]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "INSUFFICIENT_EVIDENCE"
    assert r.summary_value == "uncertain"

def test_unit_damage_visible_pass():
    r = unit_damage.run(ctx([obs(visible_unit_count=6)]))
    assert r.verdict == "PASS" and r.summary_value == "none"

# ---- units per carton ----
def test_upc_pass_single_carton():
    r = units_per_carton.run(ctx([obs(cartons_visible=1, visible_unit_count=12,
                                      count_confidence=0.9, full_contents_visible=True)]))
    assert r.verdict == "PASS" and r.summary_value == "12"

def test_upc_fail_single_carton():
    r = units_per_carton.run(ctx([obs(cartons_visible=1, visible_unit_count=10,
                                      count_confidence=0.9, full_contents_visible=True)]))
    assert r.verdict == "FAIL" and r.summary_value == "10"

def test_upc_derived_pass():
    r = units_per_carton.run(ctx([obs(cartons_visible=2, visible_unit_count=24,
                                      count_confidence=0.9, full_contents_visible=True)]))
    assert r.verdict == "PASS" and r.summary_value == "12" and r.confidence == 0.55

def test_upc_derived_mismatch_uncertain():
    r = units_per_carton.run(ctx([obs(cartons_visible=2, visible_unit_count=22,
                                      count_confidence=0.9, full_contents_visible=True)]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "CONFLICTING_EVIDENCE"

def test_upc_not_visible_uncertain():
    r = units_per_carton.run(ctx([obs()]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "INSUFFICIENT_EVIDENCE"

def test_upc_not_applicable():
    assert units_per_carton.run(ctx([obs()], units_per_carton_ordered=None)).verdict == "NOT_APPLICABLE"

# ---- missing components ----
def test_mc_not_applicable():
    assert missing_components.run(ctx([obs()], spec_components=None)).verdict == "NOT_APPLICABLE"

def test_mc_sealed_uncertain():
    r = missing_components.run(ctx([obs()]))   # not opened
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "INSUFFICIENT_EVIDENCE"
    assert "Not visible is not missing" in r.detail

def test_mc_open_all_present_pass():
    r = missing_components.run(ctx([obs(contents_open_for_inspection=True,
                                        visible_components=["bottle", "lid"])]))
    assert r.verdict == "PASS"

def test_mc_open_missing_fail():
    r = missing_components.run(ctx([obs(contents_open_for_inspection=True,
                                        full_contents_visible=True,
                                        visible_components=["bottle"])]))
    assert r.verdict == "FAIL" and "lid" in r.detail

def test_mc_partial_visibility_uncertain():
    r = missing_components.run(ctx([obs(contents_open_for_inspection=True,
                                        full_contents_visible=False,
                                        visible_components=["bottle"])]))
    assert r.verdict == "UNCERTAIN" and r.uncertainty_reason == "OCCLUSION"

# ---- other quality ----
def test_oq_other_damage_fail():
    r = other_quality.run(ctx([obs(damages=[dmg(target="unit", dtype="other")])]))
    assert r.verdict == "FAIL" and r.summary_value == "obvious_defect"

def test_oq_pass():
    r = other_quality.run(ctx([obs(), obs()]))
    assert r.verdict == "PASS" and r.summary_value == "none"