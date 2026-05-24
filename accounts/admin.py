from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from .models import User, Salary, SalaryWithdraw, WorkShift

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'full_name', 'role', 'status', 'is_verified', 'is_active']
    list_filter = ['role', 'status', 'is_verified', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'full_name', 'phone_number']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Thông tin bổ sung', {
            'fields': ('role', 'full_name', 'phone_number', 'is_verified', 'status')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Thông tin bổ sung', {
            'fields': ('role', 'full_name', 'phone_number', 'email')
        }),
    )

@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display = ['user', 'basic_salary', 'total_salary', 'withdrawn', 'available', 'last_updated']
    list_filter = ['last_updated', 'created_at']
    search_fields = ['user__username', 'user__full_name', 'user__email']
    readonly_fields = ['total_salary', 'available', 'last_updated', 'created_at']

@admin.register(SalaryWithdraw)
class SalaryWithdrawAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'requested_at', 'processed_at', 'processed_by']
    list_filter = ['status', 'requested_at', 'processed_at']
    search_fields = ['user__username', 'user__full_name', 'reason']
    readonly_fields = ['requested_at']
    
    fieldsets = (
        ('Thông tin yêu cầu', {
            'fields': ('user', 'amount', 'reason', 'requested_at')
        }),
        ('Xử lý', {
            'fields': ('status', 'processed_at', 'processed_by')
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if change and obj.status == 'approved' and not obj.processed_at:
            # Cập nhật số tiền đã rút trong bảng lương
            salary, created = Salary.objects.get_or_create(user=obj.user)
            salary.withdrawn += obj.amount
            salary.save()
            
            # Cập nhật thông tin xử lý
            obj.processed_by = request.user
            obj.processed_at = timezone.now()
        
        super().save_model(request, obj, form, change)

@admin.register(WorkShift)
class WorkShiftAdmin(admin.ModelAdmin):
    list_display = ['user', 'start_time', 'end_time', 'duration_hours', 'status']
    list_filter = ['status', 'start_time', 'duration_hours']
    search_fields = ['user__username', 'user__full_name']
    readonly_fields = ['created_at']