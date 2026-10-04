# AShare Event Opportunity Engine

**Turn A-share disclosures into linked capital events, chronological states, and evidence-backed research leads.**

A company may publish a plan, an exchange inquiry, a legal opinion, and an issuance result for the same transaction. This Python engine groups those records into one event and tracks what has actually changed, helping researchers review financing, M&A, capital expenditure, and treasury activity without counting every announcement as a new opportunity.

[Run the demo](#quick-start) · [See actual demo output](docs/demo.md) · [Methodology](docs/methodology.md) · [Tests](tests)

## See the result

The bundled **synthetic** example contains 18 announcements from 7 fictional companies. With a reference date of **2026-07-01**, the engine produces:

| Output | Demo result |
|---|---:|
| Linked capital events | 8 |
| Events in an active research window | 6 |
| Closed or historical events | 2 |
| Unclassified announcements | 1 |
| Invalid input rows | 0 |

These are reproducible demo counts, not accuracy estimates on real filings. The [full preview](docs/demo.md) shows every event, a state-transition trace, and the generated audit summary.

For example, four synthetic equity-financing disclosures become one event:

```text
2025-06-10  Plan disclosed       → planning
2025-09-18  Exchange acceptance  → review
2026-01-12  Registration         → registered
2026-04-20  Issuance result      → completed

One capital event · four source announcements · closed research lead
```

## Quick start

Requires **Python 3.10+**. The core package has no third-party runtime dependencies.

```bash
git clone https://github.com/Leo984357/ashare-event-opportunity-engine.git
cd ashare-event-opportunity-engine
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
ashare-event-engine examples/synthetic_announcements.csv \
  --financials examples/synthetic_financials.csv \
  --as-of 2026-07-01 \
  --output-dir output/demo
```

For a source-tree run without installation, use the same arguments with `PYTHONPATH=src python3 -m ashare_event_engine` in a POSIX shell.

The command writes four files:

| File | What to inspect |
|---|---|
| `announcement_classifications.csv` | Product, announcement role, confidence, and matched evidence for each disclosure |
| `capital_events.csv` | Linked disclosures, current state, and chronological state history |
| `opportunity_leads.csv` | Research status, transparent score rationale, and verification questions |
| `audit.json` | Coverage, duplicates, unclassified records, state counts, and invalid input rows |

Financial data is optional: omit `--financials` to run on announcements alone. `--as-of` sets the reference date for lead recency; when omitted, it defaults to the latest announcement date. Supply an input snapshot containing only disclosures available by your intended research date.

## How it works

```text
Announcement CSV
  → product, role, and subject classification
  → linkage by company, product, and transaction anchor
  → chronological state transitions
  → research-window status and financial signals
  → auditable CSV outputs + JSON quality summary
```

- **Separate documents from events.** A plan and its completion announcement share an event when their transaction anchors match. Ambiguous records remain separate.
- **Use document roles.** Routine reports and supporting documents provide context; substantive disclosures drive lifecycle states.
- **Preserve completed events.** Terminal states stay closed. An explicitly new plan can form a separate event.
- **Expose the reason for each lead.** Outputs include the state, evidence level, scoring rationale, and questions for human verification.
- **Keep missing data explicit.** Financial signals use disclosed fields; missing values remain missing.

The [methodology](docs/methodology.md) documents the data model, linkage rules, state transitions, financial definitions, scoring, and evaluation plan.

## Bring your own data

Required announcement columns:

| Column | Meaning |
|---|---|
| `announcement_id` | Stable disclosure identifier |
| `company_id` | Six-digit security code or another stable company identifier |
| `company_name` | Company name |
| `title` | Announcement title |
| `announcement_date` | Date in `YYYY-MM-DD` format |

Optional columns are `text` for extracted filing text and `category` for an upstream category hint. Title-only input is supported. See the [announcement fixture](examples/synthetic_announcements.csv) for a complete CSV.

Optional financial data joins on `company_id`. Fields include cash, restricted cash, operating cash flow, capex, and short-term debt; monetary fields must use a consistent unit. See the [financial fixture](examples/synthetic_financials.csv) and [field definitions](docs/methodology.md#5-financial-signals).

## Validation and research scope

After installation, run the existing classifier, linkage, state-machine, lead-scoring, and pipeline tests:

```bash
python -m unittest discover -s tests -v
```

A source-tree check in a POSIX shell is `PYTHONPATH=src python3 -m unittest discover -s tests -v`.

This is an **alpha research framework** with synthetic public examples. Before applying rules to a new period or market segment, evaluate a manually labelled sample for classification, event linkage, current-state accuracy, and terminal-state false-open rates.

A lead score is a screening score, not a transaction probability. Public disclosures can arrive after advisers have been appointed, so active events require verification of any remaining service need. The repository contains generic methods and synthetic fixtures; external research data remains separate.

## Repository map

| Path | Contents |
|---|---|
| [src/ashare_event_engine](src/ashare_event_engine) | Classification, linkage, state machine, financial features, pipeline, and CLI |
| [examples](examples) | Synthetic announcement and financial inputs |
| [docs/demo.md](docs/demo.md) | Reproduced results from the bundled example |
| [docs/methodology.md](docs/methodology.md) | Research definitions and evaluation metrics |
| [tests](tests) | Executable behavior checks |

## License

[MIT](LICENSE).
