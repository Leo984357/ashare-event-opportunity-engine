from __future__ import annotations

import hashlib
import re
from dataclasses import replace
from datetime import timedelta

from .models import CapitalEvent, ClassifiedAnnouncement
from .taxonomy import UNKNOWN


RECURRING_PRODUCTS = {"cash_management", "risk_hedging", "shareholder_service", "equity_incentive"}
LONG_CYCLE_PRODUCTS = {
    "equity_financing",
    "overseas_listing",
    "asset_securitization",
    "convertible_bond",
    "debt_financing",
    "ma_transaction",
    "capex_project",
    "industry_fund",
}


def clean_anchor(value: str) -> str:
    text = re.sub(r"[\s《》“”()（）:：,，。；;]", "", value)
    text = re.sub(r"关于|公告|进展|提示性|公司|项目", "", text)
    return text[:36] or "generic"


def first_match(title: str, patterns: tuple[str, ...]) -> str:
    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            return clean_anchor(match.group(1))
    return ""


def derive_anchor(item: ClassifiedAnnouncement) -> str:
    title = item.announcement.title
    year_match = re.search(r"(20\d{2})\s*年(?:度)?", title)
    explicit_year = year_match.group(1) if year_match else ""

    if item.product in RECURRING_PRODUCTS:
        return explicit_year or str(item.announcement.announcement_date.year)

    if item.product == "convertible_bond":
        bond = first_match(title, (r"([\u4e00-\u9fffA-Za-z0-9]{2,12}转债)",))
        if bond:
            return bond

    if item.product == "capex_project":
        project = first_match(
            title,
            (
                r"(?:投资建设|建设|扩建|新建|实施)([^，。；]{2,36}?项目)",
                r"关于([^，。；]{2,36}?项目)(?:的|建设进展|实施进展|进展|延期|结项|变更)",
            ),
        )
        if project:
            return project

    if item.product == "ma_transaction":
        target = first_match(
            title,
            (
                r"(?:购买|收购|出售)([^，。；]{2,28}?)(?:股权|资产)",
                r"与([^，。；]{2,24}?)(?:进行|实施|签署)",
            ),
        )
        if target:
            return target

    if item.product == "industry_fund":
        fund = first_match(title, (r"(?:设立|参与|投资)([^，。；]{2,30}?基金)",))
        if fund:
            return fund

    if explicit_year:
        return explicit_year

    return f"generic-{item.announcement.announcement_date.year}"


def stable_event_id(company_id: str, product: str, anchor: str, sequence: int = 1) -> str:
    raw = f"{company_id}|{product}|{anchor}|{sequence}".encode("utf-8")
    return "EV-" + hashlib.sha1(raw).hexdigest()[:12]


def compatible_anchor(new_anchor: str, old_anchor: str) -> bool:
    if new_anchor == old_anchor:
        return True
    new_generic = new_anchor.startswith("generic-")
    old_generic = old_anchor.startswith("generic-")
    return new_generic or old_generic


def link_announcements(
    classified: list[ClassifiedAnnouncement],
    max_gap_days: int = 900,
) -> list[CapitalEvent]:
    events: list[CapitalEvent] = []
    sorted_items = sorted(
        classified,
        key=lambda item: (
            item.announcement.company_id,
            item.product,
            item.announcement.announcement_date,
            item.announcement.announcement_id,
        ),
    )

    for original in sorted_items:
        if original.product == UNKNOWN or original.role == "routine":
            continue
        anchor = derive_anchor(original)
        item = replace(original, anchor=anchor)
        candidates = [
            event
            for event in events
            if event.company_id == item.announcement.company_id
            and event.product == item.product
            and item.announcement.announcement_date - event.latest_date <= timedelta(days=max_gap_days)
            and item.announcement.announcement_date >= event.first_date
        ]

        exact = [event for event in candidates if event.anchor == anchor]
        compatible = [event for event in candidates if compatible_anchor(anchor, event.anchor)]
        chosen: CapitalEvent | None = None

        if exact:
            chosen = max(exact, key=lambda event: event.latest_date)
        elif item.product in LONG_CYCLE_PRODUCTS and len(compatible) == 1:
            chosen = compatible[0]

        if chosen is None:
            same_key_count = sum(
                1
                for event in events
                if event.company_id == item.announcement.company_id
                and event.product == item.product
                and event.anchor == anchor
            )
            chosen = CapitalEvent(
                event_id=stable_event_id(item.announcement.company_id, item.product, anchor, same_key_count + 1),
                company_id=item.announcement.company_id,
                company_name=item.announcement.company_name,
                product=item.product,
                product_label=item.product_label,
                anchor=anchor,
            )
            events.append(chosen)
        elif chosen.anchor.startswith("generic-") and not anchor.startswith("generic-"):
            chosen.anchor = anchor

        chosen.announcements.append(replace(item, anchor=chosen.anchor))

    return events
