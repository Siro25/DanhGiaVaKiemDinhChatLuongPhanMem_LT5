from decimal import Decimal
from finance.models import ParkingRate

def rate_by_hour(check_in, check_out, vehicle_type):
    duration = check_out - check_in
    hours = duration.total_seconds() / 3600
    hours_ceil = int(hours) if hours == int(hours) else int(hours) + 1
    try:
        rate = ParkingRate.objects.get(vehicle_type=vehicle_type)
    except ParkingRate.DoesNotExist:
        rate = ParkingRate.objects.first()
    hourly = getattr(rate, 'hourly_rate', Decimal('0.00'))
    return (Decimal(hours_ceil) * Decimal(hourly)).quantize(Decimal('0.01'))