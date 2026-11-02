"""Shared FIFO promotion for registration, cancellation, and expiration."""


def promote(state):
    free_places = state["capacity"] - len(state["confirmed"])
    if free_places < 1 or not state["waiting"]:
        return None
    attendee = state["waiting"].pop(0)
    state["confirmed"].append(attendee)
    return attendee
