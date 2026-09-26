# 03 - One-Pager

**Status:** Working hypothesis. Targets and baseline require operator input.

## Product

A receiving workflow that compares a purchase-order line with observations from receiving images, produces separate checks for SKU, quantity, damage, and variant, and retains evidence with the resulting decision. The code is an MVP; no operational performance claim is being made.

## Measures

| Measure | Baseline | Target | Result |
|---|---|---|---|
| SKU check false-positive / false-negative rate | Not measured | Set with operators | Not measured |
| Quantity check false-positive / false-negative rate | Not measured | Set with operators | Not measured |
| Damage check false-positive / false-negative rate | Not measured | Set with operators | Not measured |
| Variant check false-positive / false-negative rate | Not measured | Set with operators | Not measured |
| `UNCERTAIN` rate by check | Not measured | Set with operators | Not measured |
| Evidence record completeness | Not measured | Define required fields and verify | Not measured |
| Review time per receiving record | Not measured | Establish baseline first | Not measured |

## Kill condition

Proposed: any check that produces a false PASS on the held-out evaluation set stays out of automatic acceptance and is routed for human review until the failure is understood and the check passes a pre-agreed re-evaluation.

This condition is intentionally conservative and must be confirmed with operators before it is treated as a product policy.

## Main risks

- Model observations may be wrong or incomplete for unseen products, packaging, lighting, or image angles.
- Synthetic reference data is not an evaluation dataset.
- A content hash does not provide immutable storage or prove who captured an image.
- The evidence contract has not yet been agreed with downstream pods.
