# Headless Agent

The canonical headless implementation is maintained at the repository root in [`backend/`](../../../backend/); source is intentionally not copied into this folder. The backend includes image extraction, SKU/quantity/damage/variant checks, deterministic decision handling, and evidence-record generation. The operational UI is in [`frontend/`](../../../frontend/).

Backend tests are in [`backend/tests/`](../../../backend/tests/). The current repository does not yet contain a held-out image fixture set or an evaluation harness, so passing unit tests must not be presented as model accuracy results.

This folder is the template-format pointer to the canonical code. Keep the root implementation authoritative to prevent duplicated code from drifting.
