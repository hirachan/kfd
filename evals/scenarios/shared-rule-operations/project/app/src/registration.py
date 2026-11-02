"""Registration operation for an in-memory event roster."""

from waitlist import promote


def register(state, attendee):
    state["waiting"].append(attendee)
    return promote(state)
