from django.contrib import admin
from .models import Vehicle

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['plate_number', 'vehicle_type', 'customer', 'check_in', 'check_out', 'status']
    list_filter = ['status', 'vehicle_type', 'service_package']
    search_fields = ['plate_number', 'customer__name']
    date_hierarchy = 'check_in'