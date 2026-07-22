from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Mapping


def parse_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()[:10]
    if not text:
        raise ValueError("announcement_date is required")
    return datetime.strptime(text, "%Y-%m-%d").date()


def first_present(row: Mapping[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return default


@dataclass(frozen=True)
class Announcement:
    announcement_id: str
    company_id: str
    company_name: str
    title: str
    announcement_date: date
    text: str = ""
    category_hint: str = ""

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "Announcement":
        announcement_id = first_present(row, "announcement_id", "announcementId")
        company_id = first_present(row, "company_id", "secCode", "code")
        company_name = first_present(row, "company_name", "secName", "name")
        title = first_present(row, "title", "announcement_title")
        date_value = first_present(row, "announcement_date", "ann_date", "date")
        if not announcement_id or not company_id or not title:
            raise ValueError("announcement_id, company_id and title are required")
        return cls(
            announcement_id=announcement_id,
            company_id=company_id.zfill(6) if company_id.isdigit() else company_id,
            company_name=company_name,
            title=title,
            announcement_date=parse_date(date_value),
            text=first_present(row, "text", "pdf_text"),
            category_hint=first_present(row, "category", "event_category"),
        )


@dataclass(frozen=True)
class ClassifiedAnnouncement:
    announcement: Announcement
    product: str
    product_label: str
    role: str
    subject: str
    state_signal: str | None
    anchor: str
    confidence: float
    matched_terms: tuple[str, ...] = ()


@dataclass(frozen=True)
class StateTransition:
    announcement_id: str
    announcement_date: date
    from_state: str
    to_state: str
    applied: bool
    reason: str


@dataclass
class CapitalEvent:
    event_id: str
    company_id: str
    company_name: str
    product: str
    product_label: str
    anchor: str
    announcements: list[ClassifiedAnnouncement] = field(default_factory=list)
    current_state: str = "unknown"
    transitions: list[StateTransition] = field(default_factory=list)

    @property
    def first_date(self) -> date:
        return min(item.announcement.announcement_date for item in self.announcements)

    @property
    def latest_date(self) -> date:
        return max(item.announcement.announcement_date for item in self.announcements)

    @property
    def representative(self) -> ClassifiedAnnouncement:
        substantive = [item for item in self.announcements if item.role not in {"routine", "support", "clarification"}]
        pool = substantive or self.announcements
        return max(pool, key=lambda item: (item.announcement.announcement_date, item.announcement.announcement_id))


@dataclass(frozen=True)
class FinancialSnapshot:
    company_id: str
    report_date: date | None = None
    revenue: float | None = None
    operating_cash_flow: float | None = None
    capex: float | None = None
    cash: float | None = None
    restricted_cash: float | None = None
    short_term_debt: float | None = None
    debt_ratio: float | None = None
    overseas_revenue_ratio: float | None = None

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "FinancialSnapshot":
        def number(*keys: str) -> float | None:
            value = first_present(row, *keys)
            if not value:
                return None
            cleaned = value.replace(",", "").replace("%", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return None

        report_date_text = first_present(row, "report_date", "report_period")
        report_date = parse_date(report_date_text) if report_date_text and len(report_date_text) >= 10 else None
        company_id = first_present(row, "company_id", "code", "secCode")
        return cls(
            company_id=company_id.zfill(6) if company_id.isdigit() else company_id,
            report_date=report_date,
            revenue=number("revenue"),
            operating_cash_flow=number("operating_cash_flow", "ocf"),
            capex=number("capex"),
            cash=number("cash"),
            restricted_cash=number("restricted_cash"),
            short_term_debt=number("short_term_debt"),
            debt_ratio=number("debt_ratio"),
            overseas_revenue_ratio=number("overseas_revenue_ratio"),
        )


@dataclass(frozen=True)
class OpportunityLead:
    opportunity_id: str
    event_id: str
    company_id: str
    company_name: str
    product: str
    service_line: str
    current_state: str
    lead_status: str
    evidence_level: str
    priority_score: int
    latest_date: date
    rationale: tuple[str, ...]
    verification_questions: tuple[str, ...]
