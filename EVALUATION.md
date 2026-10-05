Evaluation — Receiving Manager
What was measured
1. Automated test suite (deterministic layers)
88 tests, all passing (verified with `venv\Scripts\python.exe -m pytest backend\tests -q`).

Coverage: per-check logic for all 10 checks (including barcode tier, qualitygate classification, quantity conflicts, sealed-packaging behavior), decisionengine (FAIL > UNCERTAIN > PASS precedence, NOT_APPLICABLE exclusion, advisoryhandling), evidence-record hashing, org isolation (adversarial: cross-orglist/record/image access), override audit trail, and the offline all-photos-rejected → PENDING_REVIEW API path. These tests run with no network and noAPI calls — the deterministic layers are fully regression-tested.

2. Historical observed latency (Gemini; not measured on the current Groq provider)
gemini-3-flash-preview: ~9.5 s per image (one observed run)
gemini-3.1-flash-lite (fallback): ~4.7 s per image (one observed run)
Re-inspection of identical images: ~0 s (content-hash cache)Small sample; indicative only.
3. Qualitative case studies (real records produced during the build)
Damaged sealed carton (single photo): carton_damage FAIL (crushing +tear, evidence with locations); quantity/carton_count/unit_damage/components UNCERTAIN with distinct reasons (OCCLUSION /INSUFFICIENT_EVIDENCE); decision FAIL/EXCEPTION. Correct behavior: the oneprovable defect triggers the exception; everything unverifiable abstains.
Wrong SKU (photo of a printer carton vs a bottle PO): sku_identityFAIL with the label quote as evidence; variant FAIL; identity_match "no";decision FAIL/EXCEPTION. Correct catch.
Provider outage (503): fail-open verified in production — record saved,all checks UNCERTAIN/EXTRACTION_FAILED, status PENDING_REVIEW, operatorunblocked; later re-inspection after recovery replaced it with real results.
What was NOT measured (honest limitations)
No blind held-out evaluation on 50 unseen units was completed withinthe build window. Per-check accuracy, false-positive/false-negative rates,UNCERTAIN rate and abstention quality are therefore not claimed.
VLM counting accuracy was not systematically benchmarked.
Cohen's kappa between labelers was not computed (labeling round not run).
Cross-provider comparison not done. The latency observations above are historical Gemini runs; Groq has not been benchmarked.
Failure modes observed during the build
Failure	Observed	Mitigation in system
Model 503 under load	Yes (gemini-3-flash-preview, gemini-3.8-flash)	Fallback model chain; fail-open PENDING_REVIEW
Model retirement (404)	Yes (gemini-2.5-flash unavailable to new accounts)	Probe script + configurable model chain
pyzbar DLL missing on Windows	Yes	Graceful degradation to label-text tier (verified)
VLM mislabels openability/partial contents	Yes (one case: sealed-but-torn box reported open; contents partially visible)	missing_components requires full_contents_visible before FAIL — degraded to UNCERTAIN/OCCLUSION as designed
QR vs label conflict	Analyzed	Tier-1 barcode wins (documented); conflict detection = future work
Conclusion
The deterministic core (checks, policy, tenancy, override audit, qualitygate) is measured by 80+ automated tests. End-to-end behavior wasdemonstrated on real records across PASS-type, FAIL-type and fail-openpaths. Systematic accuracy measurement on a held-out set remains futurework — no accuracy figures are claimed.
