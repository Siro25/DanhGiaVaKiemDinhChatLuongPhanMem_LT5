from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

class User(AbstractUser):
    """
    Mở rộng model User mặc định của Django để quản lý nhân viên bãi đỗ xe
    """
    ROLE_CHOICES = (
        ('admin', 'Quản trị viên'),
        ('nhanvien', 'Nhân viên giữ xe'),
        ('khachhang', 'Khách hàng'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Chờ xác thực'),
        ('approved', 'Đã xác thực'),
        ('rejected', 'Từ chối'),
    )

    role = models.CharField(_('Vai trò'), max_length=20, choices=ROLE_CHOICES, default='khachhang')
    full_name = models.CharField(_('Họ và tên'), max_length=100, blank=True)
    phone_number = models.CharField(_('Số điện thoại'), max_length=15, blank=True)
    is_verified = models.BooleanField(_('Đã xác thực'), default=False)
    status = models.CharField(_('Trạng thái'), max_length=20, choices=STATUS_CHOICES, default='approved')
    
    class Meta:
        verbose_name = _('Người dùng')
        verbose_name_plural = _('Người dùng')
    
    def __str__(self):
        return self.username

class Salary(models.Model):
    """
    Model quản lý lương nhân viên
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='salary')
    basic_salary = models.DecimalField(_('Lương cơ bản'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_salary = models.DecimalField(_('Tổng lương'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    withdrawn = models.DecimalField(_('Đã rút'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    available = models.DecimalField(_('Có thể rút'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    last_updated = models.DateTimeField(_('Cập nhật lần cuối'), auto_now=True)
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Lương nhân viên')
        verbose_name_plural = _('Lương nhân viên')
    
    def save(self, *args, **kwargs):
        # available = lương cơ bản - đã rút
        # total_salary = tổng từ ca làm (chưa được admin phát)
        self.available = self.basic_salary - self.withdrawn
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'Lương {self.user.full_name or self.user.username}'

class WorkShift(models.Model):
    """
    Model quản lý ca làm việc
    """
    STATUS_CHOICES = (
        ('working', 'Đang làm việc'),
        ('finished', 'Đã hoàn thành'),
        ('interrupted', 'Bị gián đoạn'),
        ('paid', 'Đã thanh toán'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='work_shifts')
    start_time = models.DateTimeField(_('Thời gian bắt đầu'))
    end_time = models.DateTimeField(_('Thời gian kết thúc'), null=True, blank=True)
    duration_hours = models.DecimalField(_('Thời gian làm (giờ)'), max_digits=4, decimal_places=2, default=8)
    status = models.CharField(_('Trạng thái'), max_length=20, choices=STATUS_CHOICES, default='working')
    created_at = models.DateTimeField(_('Ngày tạo'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Ca làm việc')
        verbose_name_plural = _('Ca làm việc')
        ordering = ['-start_time']
    
    def __str__(self):
        return f'{self.user.full_name or self.user.username} - {self.start_time.strftime("%d/%m/%Y %H:%M")}'

class SalaryWithdraw(models.Model):
    """
    Model quản lý lịch sử rút lương
    """
    STATUS_CHOICES = (
        ('pending', 'Chờ xử lý'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdraws')
    amount = models.DecimalField(_('Số tiền rút'), max_digits=12, decimal_places=2)
    reason = models.TextField(_('Lý do rút lương'), blank=True)
    status = models.CharField(_('Trạng thái'), max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(_('Thời gian yêu cầu'), auto_now_add=True)
    processed_at = models.DateTimeField(_('Thời gian xử lý'), null=True, blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_withdraws')
    
    class Meta:
        verbose_name = _('Yêu cầu rút lương')
        verbose_name_plural = _('Yêu cầu rút lương')
        ordering = ['-requested_at']
    
    def __str__(self):
        return f'{self.user.full_name or self.user.username} - {self.amount:,.0f} VND'


class SalaryPayment(models.Model):
    """
    Model quản lý lịch sử thanh toán lương cho nhân viên
    """
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='salary_payments')
    amount = models.DecimalField(_('Số tiền thanh toán'), max_digits=12, decimal_places=2)
    shifts_count = models.IntegerField(_('Số ca làm'), default=0)
    payment_date = models.DateTimeField(_('Ngày thanh toán'), auto_now_add=True)
    paid_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='made_payments')
    notes = models.TextField(_('Ghi chú'), blank=True)
    
    class Meta:
        verbose_name = _('Thanh toán lương')
        verbose_name_plural = _('Thanh toán lương')
        ordering = ['-payment_date']
    
    def __str__(self):
        return f'Thanh toán {self.amount:,.0f} VND cho {self.employee.full_name or self.employee.username}'
