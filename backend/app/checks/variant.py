from ..models import CheckContext, CheckResult, EvidenceItem
from .base import absence, cited_latency

def _m(expected: str, observed: str) -> bool:
    e, o = expected.strip().lower(), observed.strip().lower()
    return e == o or e in o or o in e

def run(ctx: CheckContext) -> CheckResult:
    exp = ctx.po.variant
    if not exp:
        return CheckResult(check_key="variant", verdict="NOT_APPLICABLE", confidence=1.0,
                           detail="PO does not specify a variant.", evidence=[],
                           model_version=ctx.model_version)

    # Label text beats visual colour (Tier 2 vs Tier 3 evidence).
    labels = [(p, p.observation.label_variant_text) for p in ctx.observations
              if p.observation.label_variant_text]
    if labels:
        match = [(p, t) for p, t in labels if _m(exp, t)]
        if match:
            p, t = match[0]
            return CheckResult(check_key="variant", verdict="PASS", confidence=0.85,
                               detail=f"Expected variant '{exp}'; label reads '{t}'.",
                               evidence=[EvidenceItem(type="label_text", image_id=p.image_id,
                                                      quote=t,
                                                      description=f"Variant text '{t}' on label.",
                                                      strength=0.85)],
                               model_version=ctx.model_version,
                               latency_ms=cited_latency(ctx, [p.image_id]))
        p, t = labels[0]
        return CheckResult(check_key="variant", verdict="FAIL", confidence=0.8,
                           detail=f"Expected variant '{exp}' but label reads '{t}'.",
                           evidence=[EvidenceItem(type="label_text", image_id=p.image_id,
                                                  quote=t,
                                                  description=f"Label states variant '{t}'.",
                                                  strength=0.8)],
                           model_version=ctx.model_version,
                           latency_ms=cited_latency(ctx, [p.image_id]))

    colored = [p for p in ctx.observations if p.observation.dominant_product_color]
    good = [p for p in colored if p.observation.color_reliability == "good"]
    if good:
        m = [p for p in good if _m(exp, p.observation.dominant_product_color or "")]
        x = [p for p in good if not _m(exp, p.observation.dominant_product_color or "")]
        if m and not x:
            p = m[0]
            return CheckResult(check_key="variant", verdict="PASS", confidence=0.7,
                               detail=f"Expected variant '{exp}'; visible product colour is consistent.",
                               evidence=[EvidenceItem(type="visual_color", image_id=p.image_id,
                                                      description=(f"Product colour reads "
                                                                   f"'{p.observation.dominant_product_color}' "
                                                                   f"under good lighting."), strength=0.7)],
                               model_version=ctx.model_version,
                               latency_ms=cited_latency(ctx, [p.image_id]))
        if x and not m:
            p = x[0]
            return CheckResult(check_key="variant", verdict="FAIL", confidence=0.7,
                               detail=(f"Expected variant '{exp}' but products appear "
                                      f"'{p.observation.dominant_product_color}'."),
                               evidence=[EvidenceItem(type="visual_color", image_id=p.image_id,
                                                      description=(f"Product colour reads "
                                                                   f"'{p.observation.dominant_product_color}'."),
                                                                   strength=0.7)],
                               model_version=ctx.model_version,
                               latency_ms=cited_latency(ctx, [p.image_id]))
        # Images disagree on colour with good reliability on both sides.
        return CheckResult(check_key="variant", verdict="UNCERTAIN", confidence=0.4,
                           detail=f"Colour evidence conflicts across images (expected '{exp}').",
                           evidence=[EvidenceItem(type="visual_color", image_id=m[0].image_id,
                                                  description=f"'{m[0].observation.dominant_product_color}'",
                                                  strength=0.7),
                                     EvidenceItem(type="visual_color", image_id=x[0].image_id,
                                                  description=f"'{x[0].observation.dominant_product_color}'",
                                                  strength=0.7)],
                           model_version=ctx.model_version, uncertainty_reason="CONFLICTING_EVIDENCE",
                           latency_ms=cited_latency(ctx, [p.image_id for p in good]))
    if colored:
        return CheckResult(check_key="variant", verdict="UNCERTAIN", confidence=0.3,
                           detail=(f"Products visible but colour reliability is poor; "
                                   f"cannot verify variant '{exp}'."),
                           evidence=[EvidenceItem(type="visual_color", image_id=colored[0].image_id,
                                                  description="Colour unreliable due to lighting/angle.",
                                                  strength=0.3)],
                           model_version=ctx.model_version, uncertainty_reason="LOW_IMAGE_QUALITY",
                           latency_ms=cited_latency(ctx, [p.image_id for p in colored]))
    return CheckResult(check_key="variant", verdict="UNCERTAIN", confidence=0.3,
                       detail="No variant evidence (no label text, products not clearly visible).",
                       evidence=absence("No variant evidence in any image."),
                       model_version=ctx.model_version, uncertainty_reason="INSUFFICIENT_EVIDENCE",
                       latency_ms=cited_latency(ctx, [p.image_id for p in ctx.observations]))