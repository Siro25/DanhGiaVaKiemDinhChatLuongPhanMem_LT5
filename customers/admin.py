from django.contrib import admin
from .models import Customer, MonthlySubscription

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'customer_type', 'vehicle_type', 'license_plate', 'created_at']
    list_filter = ['customer_type', 'vehicle_type', 'created_at']
    search_fields = ['name', 'phone', 'license_plate']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']

@admin.register(MonthlySubscription)
class MonthlySubscriptionAdmin(admin.ModelAdmin):
    list_display = ['customer', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['customer__name', 'customer__phone']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']

