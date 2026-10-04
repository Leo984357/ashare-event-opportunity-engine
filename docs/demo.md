# Synthetic demo: actual pipeline output

This preview was produced by the repository's CLI using the bundled synthetic inputs and a fixed reference date. All companies and financial values are fictional. Counts below describe this fixture, not performance on a labelled market dataset.

## Reproduce

From the repository root after `python -m pip install -e .`:

```bash
ashare-event-engine examples/synthetic_announcements.csv \
  --financials examples/synthetic_financials.csv \
  --as-of 2026-07-01 \
  --output-dir output/demo
```

Inputs: [18 announcements](../examples/synthetic_announcements.csv) and [5 financial snapshots](../examples/synthetic_financials.csv).

## Linked events

| Fictional company | Product | Event anchor | Disclosures | Current state | Research window |
|---|---|---|---:|---|---|
| 示例芯片 | 定向增发/配股 | 2025 | 4 | `completed` | closed |
| 示例装备 | 境外上市/分拆上市 | generic-2026 | 3 | `submitted` | active |
| 示例软件 | 并购重组/资产交易 | generic-2025 | 3 | `disclosed` | active |
| 示例材料 | 重大项目/扩产 | Alpha高端材料 | 2 | `building` | active |
| 示例材料 | 重大项目/扩产 | Beta电子材料 | 1 | `planning` | active |
| 示例电子 | 现金管理 | 2026 | 1 | `authorized` | active |
| 示例通信 | 定向增发/配股 | 2025 | 1 | `completed` | closed |
| 示例通信 | 定向增发/配股 | 2026 | 1 | `planning` | active |

Two projects at the same company remain separate through their project names. The 2025 financing completion and 2026 plan at 示例通信 also remain distinct events.

The routine H-share monthly report stays in the announcement output without advancing a capital event. The shareholder-meeting notice is retained as an unclassified announcement.

## Follow one event to its sources

For 示例芯片, `capital_events.csv` contains announcement IDs `A001 | A002 | A003 | A004` and this state history:

```text
2025-06-10: unknown → planning
2025-09-18: planning → review
2026-01-12: review → registered
2026-04-20: registered → completed
```

The associated lead is marked `closed_or_historical`. The generated record preserves the completed transaction for research without reopening its lifecycle.

## Inspect a research lead

The synthetic 示例材料 Alpha project has state `building`, evidence level `A1`, and a screening score of `85`. The generated rationale combines project progress with the supplied capex and funding fields. Its verification questions ask about remaining funding, construction and cash-flow timetables, and financing channels already arranged.

The score expresses the documented screening rules. A researcher still needs to verify the actual need and existing advisers before treating a record as a service opportunity.

## Generated audit summary

```json
{
  "reference_date": "2026-07-01",
  "input_rows": 18,
  "unique_announcements": 18,
  "duplicate_announcement_ids": 0,
  "unique_companies": 7,
  "unknown_product_count": 1,
  "unknown_product_rate": 0.0556,
  "announcement_role_counts": {
    "primary": 11,
    "progress": 3,
    "completion": 2,
    "routine": 1,
    "clarification": 1
  },
  "linked_event_count": 8,
  "unknown_state_count": 0,
  "unknown_state_rate": 0.0,
  "event_state_counts": {
    "completed": 2,
    "submitted": 1,
    "disclosed": 1,
    "building": 1,
    "planning": 2,
    "authorized": 1
  },
  "opportunity_lead_count": 8,
  "lead_status_counts": {
    "active_research_window": 6,
    "closed_or_historical": 2
  },
  "financial_snapshot_count": 5,
  "invalid_input_rows": 0
}
```

[Return to the project](../README.md) · [Read the methodology](methodology.md)
