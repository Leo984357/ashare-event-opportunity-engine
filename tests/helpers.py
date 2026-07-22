from datetime import date

from ashare_event_engine.classifier import classify_announcement
from ashare_event_engine.models import Announcement


def announcement(
    announcement_id: str,
    title: str,
    announcement_date: date,
    category: str = "",
    company_id: str = "900001",
    company_name: str = "示例公司",
):
    return Announcement(
        announcement_id=announcement_id,
        company_id=company_id,
        company_name=company_name,
        title=title,
        announcement_date=announcement_date,
        category_hint=category,
    )


def classified(*args, **kwargs):
    return classify_announcement(announcement(*args, **kwargs))
