# Methodology

## 1. Unit of analysis

The engine keeps three units separate:

1. **Announcement**: one disclosure document.
2. **Capital event**: a real-world transaction or corporate action represented by several announcements.
3. **Research lead**: a transparent hypothesis that a service need may exist and requires verification.

Treating these units as interchangeable creates duplicate events and false opportunities.

## 2. Announcement classification

Each announcement receives four independent labels:

- `product`: financing, M&A, capex, fund, treasury, hedging or shareholder-service family;
- `role`: primary, progress, completion, cancellation, support, clarification or routine;
- `subject`: listed company, subsidiary, controlling shareholder, actual controller or another holder;
- `state_signal`: lifecycle evidence supported by the title.

The upstream `category` field is a hint, not ground truth. A product needs either category support or
product-specific language. Routine and support documents can be linked for provenance but cannot move an
event state.

## 3. Event linkage

An event key uses:

```text
company_id + product + disclosed transaction anchor
```

Anchors include an explicit plan year, bond name, project name, acquisition target or fund name. Generic
announcements are attached only when there is exactly one compatible recent event. Ambiguous records are
kept separate. This intentionally favors precision over recall.

Suggested evaluation:

- pairwise event-link precision and recall;
- B-cubed precision, recall and F1 for event clusters;
- over-merge and under-merge error counts by product.

## 4. State transitions

Announcements are processed in ascending date order. A state transition is applied only when:

- the announcement is substantive;
- the signal is a valid forward transition; or
- it is an explicit terminal disclosure.

Terminal states are sticky. A later plan must be represented as a new event rather than reopening a
completed transaction. Capex events allow a limited set of non-linear transitions, such as delayed to
building when construction resumes.

The exported `state_history` records every applied transition. Rejected backward transitions remain
available in the in-memory transition log with a reason.

## 5. Financial signals

Optional financial fields use the same currency unit within a row:

| Field | Definition |
|---|---|
| `revenue` | Reported revenue |
| `operating_cash_flow` | Reported operating cash flow |
| `capex` | Cash paid for fixed and other long-term assets, or another documented capex definition |
| `cash` | Reported cash and cash equivalents/monetary funds under a documented convention |
| `restricted_cash` | Disclosed restricted cash |
| `short_term_debt` | Short-term borrowings plus current maturities under a documented convention |
| `debt_ratio` | Reported debt ratio, expressed consistently across the sample |
| `overseas_revenue_ratio` | Overseas revenue divided by total revenue |

Derived variables:

```text
available_cash = max(cash - restricted_cash, 0)
free_cash_flow = operating_cash_flow - capex
short_debt_cash_cover = available_cash / short_term_debt
near_term_funding_gap_proxy
  = max(capex + short_term_debt - available_cash - max(operating_cash_flow, 0), 0)
```

The funding-gap variable is explicitly a screening proxy, not a forecast. Missing inputs produce a missing
proxy. The engine never estimates short-term debt from revenue or leverage.

## 6. Research-lead score

The 0-100 score is an additive screening score based on:

- recognized chronological state: 25;
- active lifecycle state: 20;
- recency: up to 15;
- substantive disclosure: 10;
- rule-classification confidence: 10;
- aligned disclosed financial signal: 15.

Closed events are capped at 20 and unknown states at 35. The score is not calibrated to transaction
probability and must not be interpreted as one.

Evidence levels:

- `A1`: active event plus aligned financial evidence;
- `A2`: strong active-event evidence;
- `B`: monitor or incomplete evidence;
- `C`: closed, weak or human-review case.

## 7. Gold-standard evaluation

Before deployment on a new period, label a stratified sample across product families and stages. Report:

- product-classification Macro-F1;
- support/routine exclusion precision and recall;
- event-link B-cubed F1;
- current-state accuracy;
- terminal-state false-open rate;
- unknown/abstention rate;
- research-lead Precision@20 after human review.

All evaluation dates and sample windows should be absolute and preserved in an audit file.

## 8. Limitations

- Public announcements can reveal a need only after a mandate has been awarded.
- Titles are concise and can omit material qualifiers found in the full text.
- Project names and transaction targets are not standardized across issuers.
- Rules require maintenance when regulation and disclosure language change.
- A research lead identifies questions to verify; it is neither investment advice nor a claim of available business.
