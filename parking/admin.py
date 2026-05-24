from django.contrib import admin
from .models import ParkingLot, ParkingSlot, PricingSetting

@admin.register(ParkingLot)
class ParkingLotAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'available_slots', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']

@admin.register(ParkingSlot)
class ParkingSlotAdmin(admin.ModelAdmin):
    list_display = ['slot_number', 'parking_lot', 'slot_type', 'status']
    list_filter = ['status', 'slot_type', 'parking_lot']
    search_fields = ['slot_number']

@admin.register(PricingSetting)
class PricingSettingAdmin(admin.ModelAdmin):
    list_display = ['vehicle_type', 'package_type', 'price', 'is_active', 'updated_at']
    list_filter = ['vehicle_type', 'package_type', 'is_active']
    list_editable = ['price', 'is_active']
    ordering = ['vehicle_type', 'package_type']
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('vehicle_type', 'package_type')
        }),
        ('Cấu hình giá', {
            'fields': ('price', 'is_active')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return ['vehicle_type', 'package_type']
        return []