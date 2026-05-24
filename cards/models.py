from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from customers.models import Customer
from django.utils import timezone
from decimal import Decimal

class Card(models.Model):
    """
    Model quản lý thẻ gửi xe
    """
    CARD_STATUS_CHOICES = (
        ('active', 'Đang sử dụng'),
        ('lost', 'Mất thẻ'),
        ('damaged', 'Hỏng'),
        ('locked', 'Đã khóa'),
    )
    
    card_number = models.CharField(_('Mã thẻ'), max_length=50, unique=True)
    card_type = models.CharField(_('Loại thẻ'), max_length=20, choices=(('rfid', 'RFID'), ('qr', 'QR Code')))
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='cards')
    status = models.CharField(_('Trạng thái'), max_length=20, choices=CARD_STATUS_CHOICES, default='active')
    issue_date = models.DateField(_('Ngày cấp'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Thẻ xe')
        verbose_name_plural = _('Thẻ xe')
    
    def __str__(self):
        return f"{self.card_number} - {self.get_status_display()}"

class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Chờ thanh toán'),
        ('paid', 'Đã thanh toán'),
        ('cancelled', 'Hủy'),
    ]
    METHOD_CHOICES = [
        ('cash','Tiền mặt'),
        ('card','Thẻ'),
        ('momo','MOMO'),
    ]

    vehicle = models.ForeignKey('vehicles.Vehicle', null=True, blank=True, on_delete=models.SET_NULL, related_name='card_payments')
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE)
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    method = models.CharField(max_length=12, choices=METHOD_CHOICES, default='cash')
    reference = models.CharField(max_length=120, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_transactions', verbose_name='Được tạo bởi')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.pk} - {self.total}"

    def calculate(self, rate_func):
        """
        rate_func(check_in, check_out, vehicle_type) -> Decimal base amount
        """
        if not (self.check_in and self.check_out):
            return Decimal('0.00')
        base = rate_func(self.check_in, self.check_out, getattr(self.vehicle, 'vehicle_type', None))
        self.amount = base
        self.tax = (base * Decimal('0.10')).quantize(Decimal('0.01'))  # VAT 10% example
        self.total = (self.amount + self.tax).quantize(Decimal('0.01'))
        return self.total

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notif to {self.user}: {self.title}"