from django.contrib import admin
from .models import PricingService

@admin.register(PricingService)
class PricingServiceAdmin(admin.ModelAdmin):
    list_display = ['vehicle_type', 'customer_type', 'formatted_price', 'duration', 'is_active']
    list_filter = ['vehicle_type', 'customer_type', 'is_active']
    search_fields = ['vehicle_type', 'customer_type']
    list_editable = ['is_active']
    
    def formatted_price(self, obj):
        return f"{obj.price:,.0f} VNĐ"
    formatted_price.short_description = "Giá"