# 02 - PR/FAQ

**Status:** Product hypothesis for review; not customer-validated.

## Press release draft

Receiving Manager is an early prototype for documenting supplier deliveries. It accepts purchase-order details and receiving images, evaluates identity, quantity, visible damage, and variant checks, and returns a decision with supporting evidence. The current build includes a backend workflow, a lightweight operational interface, and a hashed evidence record. It has not yet been evaluated on a held-out dataset, so it makes no accuracy or savings claims.

The intended user is a receiving operator or seller/3PL lead who needs to record what arrived and review discrepancies while the delivery is still available. The prototype is designed to preserve uncertainty for human review rather than forcing every case into a pass or fail.

## Frequently asked questions

### What problem is this trying to solve?

Receiving teams may need to compare a delivery with a purchase order and retain usable evidence of quantity, identity, variant, and visible condition. The workflow and urgency still need validation with real operators.

### Does the agent verify every unit?

Not established. The current MVP works with a single purchase-order line in its API workflow. Coverage of multiple lines, carton-level sampling, and real receiving volumes must be validated.

### How accurate is it?

Unknown. No held-out evaluation results or per-check false-positive/false-negative rates are recorded in this submission yet.

### What happens when an image is unclear or a model fails?

The system has an `UNCERTAIN` verdict for checks. The fail-open and pending-state behavior must be verified against the engineering rules and tested for the relevant failure modes before operational claims are made.

### Is the evidence record immutable or tamper-proof?

No. The implementation computes a SHA-256 content hash for the record. A content hash alone does not make storage immutable or tamper-evident.

### Has this been validated by customers or integrated with other buildathon pods?

Not yet. Customer discovery and cross-pod contract agreement are pending.

### What would stop an automated decision from being used?

The proposed kill condition is in [03-one-pager.md](03-one-pager.md). It remains subject to operator review and evaluation design.
