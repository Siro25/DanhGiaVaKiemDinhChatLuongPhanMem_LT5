from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

VEHICLE_TYPE_CHOICES = (
    ('oto', 'Ô tô'),
    ('xemay', 'Xe máy'),
    ('xedien', 'Xe điện/xe đạp điện'),
)

class Customer(models.Model):
    """
    Model quản lý thông tin khách hàng gửi xe
    """
    CUSTOMER_TYPE_CHOICES = [
        ('Khách vãng lai', 'Khách vãng lai'),
        ('Khách gửi tháng', 'Khách gửi tháng'),
    ]
    
    # Liên kết với tài khoản user
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='customer_profile', verbose_name='Tài khoản')
    
    STATUS_CHOICES = [
        ('not_registered', 'Chưa đăng ký'),
        ('awaiting_approval', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Tên khách hàng")
    phone = models.CharField(max_length=15, verbose_name="Số điện thoại")
    email = models.EmailField(max_length=100, blank=True, null=True, verbose_name="Email")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Địa chỉ")
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPE_CHOICES, verbose_name="Phân loại khách")
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES, blank=True, null=True, verbose_name="Loại xe")
    license_plate = models.CharField(max_length=20, blank=True, null=True, verbose_name="Biển số xe")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_registered', verbose_name="Trạng thái")
    created_at = models.DateTimeField(auto_now_add=True)
    # admin fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_customers', verbose_name='Được tạo bởi')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_customers', verbose_name='Nhân viên phụ trách')
    note = models.TextField(blank=True, null=True, verbose_name='Ghi chú')
    is_active = models.BooleanField(default=True, verbose_name='Hoạt động')
    
    def __str__(self):
        # Hiển thị tên + số điện thoại + username (nếu có)
        info_parts = [self.name]
        
        # Thêm số điện thoại nếu có
        if self.phone:
            info_parts.append(f"SĐT: {self.phone}")
        
        # Thêm email nếu có (để phân biệt khi SĐT trùng)
        if self.email:
            info_parts.append(f"Email: {self.email}")
        
        # Thêm gói đăng ký nếu là khách gửi tháng và có subscription
        if self.customer_type == 'Khách gửi tháng':
            from django.utils import timezone
            # Lấy subscription còn hiệu lực
            active_sub = self.subscriptions.filter(
                is_active=True,
                end_date__gte=timezone.now().date()
            ).order_by('-end_date').first()
            
            if active_sub:
                info_parts.append(f"Gói: đến {active_sub.end_date.strftime('%d/%m/%Y')}")
            else:
                info_parts.append("Gói: chưa đăng ký")
        
        # Thêm username nếu có liên kết với user
        if self.user:
            info_parts.append(f"@{self.user.username}")
        
        # Nếu không có thông tin bổ sung, thêm ID để phân biệt
        if len(info_parts) == 1:
            info_parts.append(f"ID: {self.pk}")
        
        return " | ".join(info_parts)

class MonthlySubscription(models.Model):
    """
    Model quản lý thông tin đăng ký gửi xe tháng
    """
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='subscriptions')
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.CASCADE, related_name='subscriptions', null=True, blank=True, verbose_name='Xe')
    start_date = models.DateField(verbose_name='Ngày bắt đầu')
    end_date = models.DateField(verbose_name='Ngày kết thúc')
    is_active = models.BooleanField(verbose_name='Còn hiệu lực', default=True)
    
    class Meta:
        verbose_name = 'Đăng ký gửi xe tháng'
        verbose_name_plural = 'Đăng ký gửi xe tháng'
    
    def __str__(self):
        vehicle_info = f" - {self.vehicle.plate_number}" if self.vehicle else ""
        return f"{self.customer.name}{vehicle_info} - {self.start_date} đến {self.end_date}"


class Wallet(models.Model):
    """
    Model quản lý ví điện tử của khách hàng
    """
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='wallet', verbose_name='Khách hàng')
    balance = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Số dư')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Cập nhật lần cuối')
    
    class Meta:
        verbose_name = 'Ví điện tử'
        verbose_name_plural = 'Ví điện tử'
    
    def __str__(self):
        return f"Ví của {self.customer.name} - Số dư: {self.balance:,.0f} VNĐ"


class WalletTransaction(models.Model):
    """
    Model lưu lịch sử giao dịch ví
    """
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Nạp tiền'),
        ('withdraw', 'Rút tiền'),
        ('payment', 'Thanh toán'),
        ('refund', 'Hoàn tiền'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Chờ xử lý'),
        ('completed', 'Thành công'),
        ('failed', 'Thất bại'),
        ('cancelled', 'Đã hủy'),
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions', verbose_name='Ví')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES, verbose_name='Loại giao dịch')
    amount = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Số tiền')
    balance_before = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Số dư trước')
    balance_after = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Số dư sau')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Trạng thái')
    description = models.TextField(blank=True, null=True, verbose_name='Mô tả')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian')
    
    class Meta:
        verbose_name = 'Giao dịch ví'
        verbose_name_plural = 'Giao dịch ví'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount:,.0f} VNĐ - {self.created_at.strftime('%d/%m/%Y %H:%M')}"
