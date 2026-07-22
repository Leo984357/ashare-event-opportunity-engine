"""A-share listed-company capital-event research engine."""

from .models import Announcement, CapitalEvent, FinancialSnapshot, OpportunityLead
from .pipeline import run_pipeline

__all__ = [
    "Announcement",
    "CapitalEvent",
    "FinancialSnapshot",
    "OpportunityLead",
    "run_pipeline",
]

__version__ = "0.1.0"
