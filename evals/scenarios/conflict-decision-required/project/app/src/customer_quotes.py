"""Production cancellation quotes in whole pounds."""


def cancellation_fee(hours_before_departure):
    if hours_before_departure < 24:
        raise ValueError("This quote supports early cancellations only")
    return 0
