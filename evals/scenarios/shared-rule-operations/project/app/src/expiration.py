"""Reservation expiration operation for an in-memory event roster."""

from waitlist import promote


def expire(state, attendee):
    state["confirmed"].remove(attendee)
    return promote(state)
