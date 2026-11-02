"""Cancellation operation for an in-memory event roster."""

from waitlist import promote


def cancel(state, attendee):
    state["confirmed"].remove(attendee)
    return promote(state)
