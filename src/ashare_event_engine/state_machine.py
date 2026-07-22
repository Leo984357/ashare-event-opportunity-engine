from __future__ import annotations

from .models import CapitalEvent, StateTransition
from .taxonomy import STATE_ORDER, TERMINAL_STATES


REVERSIBLE_PROJECT_TRANSITIONS = {
    ("delayed", "building"),
    ("changed", "building"),
    ("delayed", "changed"),
}


def state_rank(product: str, state: str) -> int:
    states = STATE_ORDER.get(product, ())
    try:
        return states.index(state)
    except ValueError:
        return -1


def can_transition(product: str, current: str, signal: str) -> tuple[bool, str]:
    if current == "unknown":
        return True, "first substantive state signal"
    if current == signal:
        return False, "state unchanged"
    if current in TERMINAL_STATES:
        return False, "terminal state is sticky; a new event must be linked separately"
    if signal in TERMINAL_STATES:
        return True, "explicit terminal-state disclosure"
    if product == "capex_project" and (current, signal) in REVERSIBLE_PROJECT_TRANSITIONS:
        return True, "project resumed or scope changed"
    if state_rank(product, signal) >= state_rank(product, current):
        return True, "forward lifecycle transition"
    return False, "backward transition rejected"


def advance_event(event: CapitalEvent) -> CapitalEvent:
    event.current_state = "unknown"
    event.transitions = []
    ordered = sorted(
        event.announcements,
        key=lambda item: (item.announcement.announcement_date, item.announcement.announcement_id),
    )

    for item in ordered:
        signal = item.state_signal
        if not signal:
            continue
        current = event.current_state
        applied, reason = can_transition(event.product, current, signal)
        event.transitions.append(
            StateTransition(
                announcement_id=item.announcement.announcement_id,
                announcement_date=item.announcement.announcement_date,
                from_state=current,
                to_state=signal,
                applied=applied,
                reason=reason,
            )
        )
        if applied:
            event.current_state = signal

    return event


def advance_events(events: list[CapitalEvent]) -> list[CapitalEvent]:
    return [advance_event(event) for event in events]
