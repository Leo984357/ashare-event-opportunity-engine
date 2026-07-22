# Progress Report

## Release objective

Create a sanitized, reproducible public implementation of an A-share capital-event state machine without
publishing licensed data, employer material or real client-opportunity rankings.

## Implemented

- Rule-based product, role and subject classification.
- Event linkage using company, product, disclosed year and transaction anchors.
- Chronological state transitions with sticky terminal states.
- Transparent research-lead scoring and verification questions.
- Optional financial-signal layer using only reported inputs.
- CSV outputs plus audit JSON.
- Synthetic examples and regression tests for known false-positive cases.

## Current limitations

- The public example is synthetic and is not an empirical accuracy benchmark.
- Full-text semantic extraction and table parsing are outside the first release.
- A manually labelled gold-standard dataset is required before production use.

## Next empirical step

Label a stratified sample of public announcements and report product Macro-F1, event-link B-cubed F1,
state accuracy and research-lead Precision@20.
