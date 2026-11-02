"""Cancel a confirmed booking when its departure is far enough away."""


def cancel_booking(booking, hours_before_departure):
    if booking["status"] != "confirmed" or hours_before_departure < 24:
        return False
    booking["status"] = "cancelled"
    return True
