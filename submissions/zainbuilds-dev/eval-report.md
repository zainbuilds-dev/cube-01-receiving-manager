# Evaluation Report

**Status:** Not evaluated. No accuracy or agreement numbers are available in this repository.

## Evaluation method to complete

Use a held-out set of receiving images that was not used to develop prompts, thresholds, or checks. Record image provenance and define a label rubric before inference. Have two independent labellers assign the ground truth per check, then adjudicate disagreements without using the model's answer as ground truth. Report the agreement method and value, including the number of examples and class distribution.

Run the frozen system once on the held-out set. For SKU, quantity, damage, and variant, report the confusion matrix and false-positive and false-negative rates separately. Report `UNCERTAIN` cases separately rather than counting them as correct. Break down failure modes by image quality, packaging, and other relevant conditions when sample size permits.

## Results

| Check | Evaluated examples | False positives | False negatives | Uncertain | Status |
|---|---:|---:|---:|---:|---|
| SKU | Not available | Not measured | Not measured | Not measured | Pending dataset |
| Quantity | Not available | Not measured | Not measured | Not measured | Pending dataset |
| Damage | Not available | Not measured | Not measured | Not measured | Pending dataset |
| Variant | Not available | Not measured | Not measured | Not measured | Pending dataset |

Two-labeller agreement: not measured.

## Known limitations

The repository includes synthetic/reference data, not a labeled held-out image evaluation set. No measured performance, customer validation, or operational savings should be inferred from the unit tests or demo workflow.
