# AShare Event Opportunity Engine

Evidence-backed state tracking for capital-market announcements of A-share listed companies.

This project turns noisy disclosure records into auditable research objects:

```text
announcement
  -> product and announcement-role classification
  -> announcements linked to the same capital event
  -> chronological state transitions
  -> active-window and service-opportunity research leads
  -> audit report and human-review queue
```

The repository contains only generic methods and synthetic examples. It does not contain licensed
financial data, downloaded filings, employer material, real client lists, or investment recommendations.

## Why this is different from keyword counting

A listed company can publish dozens of documents around one transaction. A plan, an exchange inquiry,
a legal opinion and an issuance result are not four independent opportunities. This engine:

- links related announcements into one event;
- separates primary disclosures from routine reports, intermediary opinions and regulatory clarifications;
- processes state transitions in date order;
- keeps terminal states closed unless an explicitly new event is identified;
- exposes confidence, matched evidence and verification questions instead of outputting an unexplained score.

## Quick start

Python 3.10 or newer is required. The core package has no third-party runtime dependency.

```bash
python -m pip install -e .
ashare-event-engine examples/synthetic_announcements.csv --output-dir output
```

Generated files:

- `announcement_classifications.csv`: one announcement per row;
- `capital_events.csv`: one linked capital event per row;
- `opportunity_leads.csv`: one research lead per event;
- `audit.json`: coverage, duplicates, abstentions and state-quality checks.

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Input schema

Required columns:

| Column | Meaning |
|---|---|
| `announcement_id` | Stable disclosure identifier |
| `company_id` | Six-digit security code or another stable company identifier |
| `company_name` | Company name |
| `title` | Announcement title |
| `announcement_date` | `YYYY-MM-DD` |

Optional columns:

| Column | Meaning |
|---|---|
| `text` | Extracted filing text; title-only processing is supported |
| `category` | Upstream category hint such as `定增_配股`; it is evidence, not ground truth |

An optional financial CSV can be supplied with `--financials`. Its stable identifier is
`company_id`; supported fields are documented in [methodology.md](docs/methodology.md).

## Research boundaries

- A lead score is a transparent screening score, not a transaction probability.
- Public disclosure usually arrives after advisers have been appointed. An active event does not imply
  that a mandate remains available.
- Missing financial values remain missing. The engine does not estimate short-term debt from leverage or
  substitute zero for undisclosed values.
- Rules should be evaluated on a manually labelled sample before use on a new period or market segment.

See [methodology.md](docs/methodology.md) for the data model, state logic and suggested evaluation metrics.

## License

MIT. See [LICENSE](LICENSE).
Evidence-backed state machine for A-share listed-company capital events and service opportunity research
