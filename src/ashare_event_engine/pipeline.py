from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Any

from .classifier import classify_announcement
from .linker import link_announcements
from .models import Announcement, ClassifiedAnnouncement, FinancialSnapshot, OpportunityLead
from .opportunity import build_opportunity_leads
from .state_machine import advance_events
from .taxonomy import UNKNOWN


def deduplicate_announcements(announcements: Iterable[Announcement]) -> tuple[list[Announcement], int]:
    by_id: dict[str, Announcement] = {}
    duplicate_count = 0
    for announcement in announcements:
        if announcement.announcement_id in by_id:
            duplicate_count += 1
        by_id[announcement.announcement_id] = announcement
    return list(by_id.values()), duplicate_count


def run_pipeline(
    announcements: Iterable[Announcement],
    financials: dict[str, FinancialSnapshot] | None = None,
    as_of: date | None = None,
) -> dict[str, Any]:
    unique, duplicate_count = deduplicate_announcements(announcements)
    classified = [classify_announcement(item) for item in unique]
    events = advance_events(link_announcements(classified))
    reference_date = as_of or max((item.announcement_date for item in unique), default=date.today())
    leads = build_opportunity_leads(events, reference_date, financials)

    role_counts = Counter(item.role for item in classified)
    state_counts = Counter(event.current_state for event in events)
    lead_status_counts = Counter(lead.lead_status for lead in leads)
    unknown_products = sum(item.product == UNKNOWN for item in classified)
    unknown_states = sum(event.current_state == "unknown" for event in events)

    audit = {
        "reference_date": reference_date.isoformat(),
        "input_rows": len(unique) + duplicate_count,
        "unique_announcements": len(unique),
        "duplicate_announcement_ids": duplicate_count,
        "unique_companies": len({item.company_id for item in unique}),
        "unknown_product_count": unknown_products,
        "unknown_product_rate": round(unknown_products / len(classified), 4) if classified else 0.0,
        "announcement_role_counts": dict(role_counts),
        "linked_event_count": len(events),
        "unknown_state_count": unknown_states,
        "unknown_state_rate": round(unknown_states / len(events), 4) if events else 0.0,
        "event_state_counts": dict(state_counts),
        "opportunity_lead_count": len(leads),
        "lead_status_counts": dict(lead_status_counts),
        "financial_snapshot_count": len(financials or {}),
    }
    return {"classified": classified, "events": events, "leads": leads, "audit": audit}


def read_announcements(path: Path) -> tuple[list[Announcement], list[dict[str, str]]]:
    announcements: list[Announcement] = []
    errors: list[dict[str, str]] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row_number, row in enumerate(csv.DictReader(handle), start=2):
            try:
                announcements.append(Announcement.from_mapping(row))
            except (ValueError, TypeError) as exc:
                errors.append({"row_number": str(row_number), "error": str(exc)})
    return announcements, errors


def read_financials(path: Path | None) -> dict[str, FinancialSnapshot]:
    if path is None:
        return {}
    snapshots: dict[str, FinancialSnapshot] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            snapshot = FinancialSnapshot.from_mapping(row)
            if snapshot.company_id:
                snapshots[snapshot.company_id] = snapshot
    return snapshots


def classified_row(item: ClassifiedAnnouncement) -> dict[str, str | float]:
    ann = item.announcement
    return {
        "announcement_id": ann.announcement_id,
        "company_id": ann.company_id,
        "company_name": ann.company_name,
        "announcement_date": ann.announcement_date.isoformat(),
        "title": ann.title,
        "category_hint": ann.category_hint,
        "product": item.product,
        "product_label": item.product_label,
        "role": item.role,
        "subject": item.subject,
        "state_signal": item.state_signal or "",
        "confidence": item.confidence,
        "matched_terms": " | ".join(item.matched_terms),
    }


def event_row(event) -> dict[str, str | int]:
    applied = [transition for transition in event.transitions if transition.applied]
    return {
        "event_id": event.event_id,
        "company_id": event.company_id,
        "company_name": event.company_name,
        "product": event.product,
        "product_label": event.product_label,
        "event_anchor": event.anchor,
        "current_state": event.current_state,
        "first_date": event.first_date.isoformat(),
        "latest_date": event.latest_date.isoformat(),
        "announcement_count": len(event.announcements),
        "support_announcement_count": sum(item.role in {"support", "clarification"} for item in event.announcements),
        "representative_title": event.representative.announcement.title,
        "announcement_ids": " | ".join(item.announcement.announcement_id for item in event.announcements),
        "state_history": " | ".join(
            f"{transition.announcement_date.isoformat()}:{transition.from_state}->{transition.to_state}"
            for transition in applied
        ),
    }


def lead_row(lead: OpportunityLead) -> dict[str, str | int]:
    row = asdict(lead)
    row["latest_date"] = lead.latest_date.isoformat()
    row["rationale"] = " | ".join(lead.rationale)
    row["verification_questions"] = " | ".join(lead.verification_questions)
    return row


def write_csv_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(result: Mapping[str, Any], output_dir: Path, input_errors: list[dict[str, str]] | None = None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv_rows(output_dir / "announcement_classifications.csv", [classified_row(item) for item in result["classified"]])
    write_csv_rows(output_dir / "capital_events.csv", [event_row(item) for item in result["events"]])
    write_csv_rows(output_dir / "opportunity_leads.csv", [lead_row(item) for item in result["leads"]])
    audit = dict(result["audit"])
    audit["invalid_input_rows"] = len(input_errors or [])
    if input_errors:
        audit["input_errors"] = input_errors
    (output_dir / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
