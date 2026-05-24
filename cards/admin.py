from django.contrib import admin
from .models import PaymentTransaction

@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ('pk','vehicle','customer','total','status','method','created_at')
    list_filter = ('status','method','created_at')
    search_fields = ('vehicle__plate_number','customer__name','reference')