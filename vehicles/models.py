from django.db import models
from django.utils.translation import gettext_lazy as _
from customers.models import Customer
from django.conf import settings

class Vehicle(models.Model):
    VEHICLE_TYPE_CHOICES = [
        ('car', 'Ô tô'),
        ('motorcycle', 'Xe máy'),
        ('bicycle', 'Xe đạp'),
        ('truck', 'Xe tải'),
        ('taxi', 'Taxi'),
    ]

    SERVICE_PACKAGE_CHOICES = [
        ('daily', 'Vé ngày'),
        ('monthly', 'Vé tháng'),
        ('guest', 'Vãng lai'),
    ]

    STATUS_CHOICES = [
        ('in', 'Đang gửi'),
        ('out', 'Đã rời'),
    ]

    plate_number = models.CharField(_('Biển số xe'), max_length=20, unique=True)
    vehicle_type = models.CharField(_('Loại xe'), max_length=20, choices=VEHICLE_TYPE_CHOICES, default='car')
    color = models.CharField(_('Màu xe'), max_length=30, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles')
    service_package = models.CharField(_('Gói dịch vụ'), max_length=10, choices=SERVICE_PACKAGE_CHOICES, default='monthly')
    parking_slot = models.CharField(_('Vị trí'), max_length=30, blank=True)
    # Liên kết với bãi xe
    parking_lot = models.ForeignKey('parking.ParkingLot', on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles', verbose_name='Bãi xe')
    image = models.ImageField(_('Hình ảnh'), upload_to='vehicles/', null=True, blank=True)
    check_in = models.DateTimeField(_('Thời gian vào'), auto_now_add=True)
    check_out = models.DateTimeField(_('Thời gian ra'), null=True, blank=True)
    status = models.CharField(_('Trạng thái'), max_length=5, choices=STATUS_CHOICES, default='in')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # admin fields: nhân viên xử lý
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_vehicles', verbose_name='Được tạo bởi')
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='handled_vehicles', verbose_name='Nhân viên xử lý')
    # Approval fields
    approved = models.BooleanField(default=False, verbose_name='Đã duyệt')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_vehicles', verbose_name='Người duyệt')

    class Meta:
        verbose_name = _('Phương tiện')
        verbose_name_plural = _('Phương tiện')
        ordering = ['-check_in']

    def __str__(self):
        return f"{self.plate_number} ({self.get_vehicle_type_display()})"

# Signal để tự động tạo transaction khi thêm vehicle
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Vehicle)
def create_transaction_on_vehicle_add(sender, instance, created, **kwargs):
    """Tự động tạo PaymentTransaction khi thêm vehicle mới"""
    if created and instance.customer and instance.customer.customer_type == 'Khách gửi tháng':
        from django.utils import timezone
        from cards.models import PaymentTransaction
        from parking.models import PricingSetting
        from decimal import Decimal
        
        print(f"🚗 Signal triggered for vehicle {instance.id} - customer: {instance.customer.name}")
        
        # Kiểm tra xem đã có transaction cho vehicle này chưa để tránh duplicate
        existing_transaction = PaymentTransaction.objects.filter(
            vehicle=instance,
            customer=instance.customer
        ).first()
        
        if existing_transaction:
            print(f"❌ Transaction đã tồn tại cho vehicle {instance.id}, bỏ qua. Transaction ID: {existing_transaction.id}")
            return
        
        print(f"✅ Tạo transaction mới cho vehicle {instance.id}")
        
        # Cập nhật status customer thành 'awaiting_approval'
        instance.customer.status = 'awaiting_approval'
        instance.customer.save()
        
        # Tính toán số tiền
        vehicle_type_map = {
            'motorcycle': 'motorcycle',
            'car': 'car',
            'bicycle': 'bicycle',
            'Xe máy': 'motorcycle',
            'Ô tô': 'car',
            'Xe đạp': 'bicycle'
        }
        
        pricing_vehicle_type = vehicle_type_map.get(instance.vehicle_type, 'motorcycle')
        try:
            price = PricingSetting.get_price(pricing_vehicle_type, 'monthly')
        except:
            # Fallback prices nếu không có PricingSetting
            fallback_prices = {
                'motorcycle': 100000,
                'car': 800000, 
                'bicycle': 50000
            }
            price = fallback_prices.get(pricing_vehicle_type, 100000)
        
        # Tạo transaction
        transaction = PaymentTransaction.objects.create(
            customer=instance.customer,
            vehicle=instance,
            check_in=instance.check_in,
            check_out=None,  # Gói tháng không có check_out ngay
            amount=Decimal(str(price)),
            total=Decimal(str(price)),
            method='cash',
            status='pending',  # Chờ thanh toán
            reference=f'MONTHLY-{instance.customer.id}-{timezone.now().strftime("%Y%m%d%H%M%S")}',
            created_by=instance.created_by
        )