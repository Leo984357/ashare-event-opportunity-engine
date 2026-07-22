from __future__ import annotations

import hashlib
from datetime import date

from .financial_features import financial_alignment
from .models import CapitalEvent, FinancialSnapshot, OpportunityLead
from .taxonomy import ACTIVE_STATES, SERVICE_LINES, TERMINAL_STATES


VERIFY_QUESTIONS = {
    "equity_financing": (
        "What is the current review or issuance stage?",
        "Which sponsor and lead underwriter have already been appointed?",
        "Is there a remaining distribution, follow-on financing or investor-introduction window?",
    ),
    "overseas_listing": (
        "Has an application actually been filed, or is the company still preparing?",
        "Which domestic and overseas advisers have been appointed?",
        "What approvals, filing steps and timetable remain?",
    ),
    "asset_securitization": (
        "What assets, cash flows and legal rights form the securitization pool?",
        "What review, registration, valuation and issuance steps remain?",
        "Which manager, custodian, adviser and distribution institutions are already appointed?",
    ),
    "convertible_bond": (
        "What are the registration, issuance, redemption and maturity dates?",
        "Which intermediaries are already mandated?",
        "Does the company face a refinancing or distribution requirement?",
    ),
    "debt_financing": (
        "What are the registered quota, debt maturity profile and intended use of proceeds?",
        "Which underwriters and banks are incumbent?",
        "Is the need a new mandate, refinancing or secondary distribution?",
    ),
    "ma_transaction": (
        "Is the transaction still being planned, under review, closing or already completed?",
        "Who is the financial adviser and is there follow-on financing?",
        "What consideration, integration and regulatory issues remain?",
    ),
    "capex_project": (
        "What are the total investment, committed funding and remaining funding gap?",
        "What is the construction, ramp-up and cash-flow timetable?",
        "Which bank, bond, equity or fund channels are already arranged?",
    ),
    "industry_fund": (
        "Have the GP, LP, custodian and administrator been selected?",
        "Is the fund planned, registered, investing or exiting?",
        "What project-sourcing and exit services are still required?",
    ),
    "cash_management": (
        "How much cash is unrestricted after debt service and committed capex?",
        "What board authorization, duration and risk constraints apply?",
        "Which incumbent products and institutions are already used?",
    ),
    "risk_hedging": (
        "What is the actual currency, commodity or interest-rate exposure?",
        "What hedge ratio and authorization are currently in place?",
        "Is the objective accounting hedging, economic hedging or liquidity management?",
    ),
    "shareholder_service": (
        "Which shareholder is the decision-maker and what restrictions apply?",
        "What are the pledge, unlock, disposal or repurchase timetable and size?",
        "What market-capacity and compliance constraints remain?",
    ),
    "equity_incentive": (
        "What are the grant, vesting and exercise schedules?",
        "Which plan-design, account and execution services remain open?",
        "What board, tax and disclosure constraints apply?",
    ),
}


def opportunity_id(event_id: str, service_line: str) -> str:
    raw = f"{event_id}|{service_line}".encode("utf-8")
    return "OP-" + hashlib.sha1(raw).hexdigest()[:12]


def event_has_substantive_evidence(event: CapitalEvent) -> bool:
    return any(item.role in {"primary", "progress", "completion", "cancellation"} for item in event.announcements)


def build_opportunity_lead(
    event: CapitalEvent,
    as_of: date,
    financial: FinancialSnapshot | None = None,
) -> OpportunityLead:
    service_line = SERVICE_LINES[event.product]
    age_days = max((as_of - event.latest_date).days, 0)
    active = event.current_state in ACTIVE_STATES
    terminal = event.current_state in TERMINAL_STATES
    substantive = event_has_substantive_evidence(event)
    mean_confidence = sum(item.confidence for item in event.announcements) / len(event.announcements)
    aligned, financial_reasons = financial_alignment(event.product, financial)

    score = 0
    rationale: list[str] = []
    if event.current_state != "unknown":
        score += 25
        rationale.append(f"chronological disclosures support current state '{event.current_state}'")
    if active:
        score += 20
        rationale.append("the event is in an active lifecycle state")
    if age_days <= 90:
        score += 15
        rationale.append(f"latest substantive evidence is {age_days} days old")
    elif age_days <= 365:
        score += 10
        rationale.append(f"latest substantive evidence is within one year ({age_days} days)")
    elif age_days <= 730:
        score += 4
        rationale.append(f"latest evidence is older ({age_days} days)")
    if substantive:
        score += 10
        rationale.append("at least one primary or progress disclosure is present")
    if mean_confidence >= 0.75:
        score += 10
        rationale.append(f"mean rule-classification confidence is {mean_confidence:.2f}")
    if aligned is True:
        score += 15
        rationale.extend(financial_reasons)
    elif aligned is False:
        rationale.extend(financial_reasons)
    else:
        rationale.append(financial_reasons[0])

    if terminal:
        score = min(score, 20)
        lead_status = "closed_or_historical"
        rationale.append("terminal disclosure closes the current event; a later plan must be linked as a new event")
    elif event.current_state == "unknown":
        score = min(score, 35)
        lead_status = "human_review"
    elif active and age_days <= 365:
        lead_status = "active_research_window"
    else:
        lead_status = "monitor"

    if event.current_state in {"registered", "approved", "issuing", "closing"}:
        rationale.append("the transaction is advanced, so core advisers may already be appointed; only residual service windows should be inferred")

    if score >= 75 and aligned is True and active:
        evidence_level = "A1"
    elif score >= 60 and active:
        evidence_level = "A2"
    elif score >= 40:
        evidence_level = "B"
    else:
        evidence_level = "C"

    return OpportunityLead(
        opportunity_id=opportunity_id(event.event_id, service_line),
        event_id=event.event_id,
        company_id=event.company_id,
        company_name=event.company_name,
        product=event.product,
        service_line=service_line,
        current_state=event.current_state,
        lead_status=lead_status,
        evidence_level=evidence_level,
        priority_score=score,
        latest_date=event.latest_date,
        rationale=tuple(rationale),
        verification_questions=VERIFY_QUESTIONS[event.product],
    )


def build_opportunity_leads(
    events: list[CapitalEvent],
    as_of: date,
    financials: dict[str, FinancialSnapshot] | None = None,
) -> list[OpportunityLead]:
    financials = financials or {}
    leads = [build_opportunity_lead(event, as_of, financials.get(event.company_id)) for event in events]
    return sorted(leads, key=lambda lead: (-lead.priority_score, -lead.latest_date.toordinal(), lead.company_id))
