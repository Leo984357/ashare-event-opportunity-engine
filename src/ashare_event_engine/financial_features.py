from __future__ import annotations

from .models import FinancialSnapshot


def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def available_cash(snapshot: FinancialSnapshot) -> float | None:
    if snapshot.cash is None:
        return None
    restricted = snapshot.restricted_cash or 0.0
    return max(snapshot.cash - restricted, 0.0)


def derived_financial_features(snapshot: FinancialSnapshot) -> dict[str, float | None]:
    usable_cash = available_cash(snapshot)
    free_cash_flow = None
    if snapshot.operating_cash_flow is not None and snapshot.capex is not None:
        free_cash_flow = snapshot.operating_cash_flow - snapshot.capex

    funding_gap_proxy = None
    required_inputs = (snapshot.capex, snapshot.short_term_debt, usable_cash, snapshot.operating_cash_flow)
    if all(value is not None for value in required_inputs):
        funding_gap_proxy = max(
            (snapshot.capex or 0.0)
            + (snapshot.short_term_debt or 0.0)
            - (usable_cash or 0.0)
            - max(snapshot.operating_cash_flow or 0.0, 0.0),
            0.0,
        )

    return {
        "available_cash": usable_cash,
        "available_cash_to_revenue": safe_ratio(usable_cash, snapshot.revenue),
        "short_debt_cash_cover": safe_ratio(usable_cash, snapshot.short_term_debt),
        "capex_to_revenue": safe_ratio(snapshot.capex, snapshot.revenue),
        "free_cash_flow": free_cash_flow,
        "near_term_funding_gap_proxy": funding_gap_proxy,
        "debt_ratio": snapshot.debt_ratio,
        "overseas_revenue_ratio": snapshot.overseas_revenue_ratio,
    }


def financial_alignment(product: str, snapshot: FinancialSnapshot | None) -> tuple[bool | None, tuple[str, ...]]:
    if snapshot is None:
        return None, ("No financial snapshot supplied; event evidence is evaluated on its own.",)

    features = derived_financial_features(snapshot)
    reasons: list[str] = []
    aligned = False

    if product == "cash_management":
        cash_ratio = features["available_cash_to_revenue"]
        free_cash_flow = features["free_cash_flow"]
        if cash_ratio is not None and cash_ratio >= 0.20:
            aligned = True
            reasons.append(f"available cash/revenue is {cash_ratio:.1%}")
        if free_cash_flow is not None and free_cash_flow < 0:
            aligned = False
            reasons.append("free cash flow is negative, so reported cash may not be truly idle")

    elif product in {"equity_financing", "convertible_bond", "debt_financing", "capex_project"}:
        capex_ratio = features["capex_to_revenue"]
        gap = features["near_term_funding_gap_proxy"]
        if capex_ratio is not None and capex_ratio >= 0.15:
            aligned = True
            reasons.append(f"capex/revenue is {capex_ratio:.1%}")
        if gap is not None and gap > 0:
            aligned = True
            reasons.append("disclosed cash, operating cash flow and short debt imply a positive near-term funding-gap proxy")

    elif product == "risk_hedging":
        overseas_ratio = features["overseas_revenue_ratio"]
        if overseas_ratio is not None and overseas_ratio >= 0.20:
            aligned = True
            reasons.append(f"overseas revenue ratio is {overseas_ratio:.1%}")

    elif product == "ma_transaction":
        cash_cover = features["short_debt_cash_cover"]
        if cash_cover is not None:
            aligned = True
            reasons.append(f"available-cash/short-debt coverage is {cash_cover:.2f}x; transaction funding still requires review")

    if not reasons:
        reasons.append("available financial fields do not provide an additional directional signal")
    return aligned, tuple(reasons)
