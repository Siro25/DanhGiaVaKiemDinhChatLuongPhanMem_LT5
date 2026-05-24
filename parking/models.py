from django.db import models
from django.utils.translation import gettext_lazy as _
from vehicles.models import Vehicle
from cards.models import Card
from finance.models import ParkingRate

class ParkingLot(models.Model):
    """
    Model quản lý thông tin bãi đỗ xe
    """
    STATUS_CHOICES = [
        ('active', 'Hoạt động'),
        ('maintenance', 'Bảo trì'),
        ('closed', 'Đóng cửa'),
    ]
    
    ALLOWED_VEHICLE_TYPES = [
        ('small', 'Xe nhỏ (Xe máy, Xe đạp)'),
        ('large', 'Xe to (Ô tô, Xe tải, Taxi)'),
        ('all', 'Tất cả loại xe'),
    ]
    
    name = models.CharField(_('Tên bãi đỗ xe'), max_length=100)
    description = models.TextField(_('Mô tả'), blank=True)
    capacity = models.PositiveIntegerField(_('Sức chứa'))
    available_slots = models.PositiveIntegerField(_('Chỗ trống hiện tại'))
    location = models.CharField(_('Vị trí'), max_length=200, blank=True)
    status = models.CharField(_('Trạng thái'), max_length=20, choices=STATUS_CHOICES, default='active')
    allowed_vehicle_types = models.CharField(_('Loại xe được phép'), max_length=20, choices=ALLOWED_VEHICLE_TYPES, default='all')
    hourly_rate = models.DecimalField(_('Giá theo giờ'), max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Bãi đỗ xe')
        verbose_name_plural = _('Bãi đỗ xe')
    
    def __str__(self):
        return f"{self.name} ({self.available_slots}/{self.capacity})"
    
    def get_occupancy_rate(self):
        """Tính tỷ lệ lấp đầy"""
        if self.capacity > 0:
            return ((self.capacity - self.available_slots) / self.capacity) * 100
        return 0
    
    @property
    def total_slots(self):
        """Tổng số vị trí đỗ xe trong bãi"""
        return self.slots.count()
    
    @property
    def available_slots_count(self):
        """Số vị trí trống"""
        return self.slots.filter(status='available').count()
    
    @property
    def occupied_slots(self):
        """Số vị trí đang có xe - Đếm theo ParkingRecord đang active"""
        # Đếm số xe đang trong bãi (chưa có exit_time)
        return self.parking_records.filter(exit_time__isnull=True).count()
    
    @property
    def maintenance_slots(self):
        """Số vị trí đang bảo trì"""
        return self.slots.filter(status='maintenance').count()
    
    @property
    def occupancy_rate(self):
        """Tỷ lệ sử dụng (%)"""
        total = self.total_slots
        if total > 0:
            return (self.occupied_slots / total) * 100
        return 0

class ParkingSlot(models.Model):
    """
    Model quản lý vị trí đỗ xe cụ thể
    """
    STATUS_CHOICES = [
        ('available', 'Trống'),
        ('occupied', 'Đã có xe'),
        ('reserved', 'Đã đặt chỗ'),
        ('maintenance', 'Bảo trì'),
    ]
    
    SLOT_TYPE_CHOICES = [
        ('car', 'Ô tô'),
        ('motorcycle', 'Xe máy'), 
        ('bicycle', 'Xe đạp'),
        ('disabled', 'Người khuyết tật'),
        ('vip', 'VIP'),
    ]
    
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='slots')
    slot_number = models.CharField(_('Số vị trí'), max_length=20)
    slot_type = models.CharField(_('Loại vị trí'), max_length=20, choices=SLOT_TYPE_CHOICES, default='car')
    status = models.CharField(_('Trạng thái'), max_length=20, choices=STATUS_CHOICES, default='available')
    floor = models.PositiveIntegerField(_('Tầng'), default=1)
    section = models.CharField(_('Khu vực'), max_length=50, blank=True)
    notes = models.TextField(_('Ghi chú'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Vị trí đỗ xe')
        verbose_name_plural = _('Vị trí đỗ xe')
        unique_together = ['parking_lot', 'slot_number']
    
    def __str__(self):
        return f"{self.parking_lot.name} - {self.slot_number}"

class ParkingRecord(models.Model):
    """
    Model quản lý lượt xe ra/vào
    """
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='parking_records')
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='parking_records')
    parking_lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='parking_records')
    entry_time = models.DateTimeField(_('Thời gian vào'))
    exit_time = models.DateTimeField(_('Thời gian ra'), null=True, blank=True)
    fee = models.DecimalField(_('Phí gửi xe'), max_digits=10, decimal_places=2, null=True, blank=True)
    is_paid = models.BooleanField(_('Đã thanh toán'), default=False)
    parking_rate = models.ForeignKey(ParkingRate, on_delete=models.SET_NULL, null=True, related_name='parking_records')
    notes = models.TextField(_('Ghi chú'), blank=True)
    
    class Meta:
        verbose_name = _('Lượt gửi xe')
        verbose_name_plural = _('Lượt gửi xe')
    
    def __str__(self):
        return f"{self.vehicle.license_plate} - {self.entry_time}"
    
    def calculate_fee(self):
        """
        Tính phí gửi xe dựa trên thời gian vào/ra và biểu phí
        """
        if not self.exit_time or not self.parking_rate:
            return None
        
        # Tính toán thời gian gửi xe
        duration = self.exit_time - self.entry_time
        hours = duration.total_seconds() / 3600
        
        # Tính phí theo biểu phí
        if self.parking_rate.rate_type == 'hourly':
            return self.parking_rate.rate * hours
        elif self.parking_rate.rate_type == 'daily':
            days = hours / 24
            return self.parking_rate.rate * days
        else:
            return self.parking_rate.rate


class PricingSetting(models.Model):
    """Cấu hình bảng giá"""
    VEHICLE_TYPES = [
        ('car', 'Ô tô'),
        ('motorcycle', 'Xe máy'),
        ('bicycle', 'Xe đạp'),
    ]
    
    PACKAGE_TYPES = [
        ('monthly', 'Vé tháng'),
        ('hourly', 'Vé theo lượt'),
    ]
    
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES)
    price = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['vehicle_type', 'package_type']
        verbose_name = "Cấu hình giá"
        verbose_name_plural = "Cấu hình giá"
    
    def __str__(self):
        return f"{self.get_vehicle_type_display()} - {self.get_package_type_display()}: {self.price:,.0f} VNĐ"

    @classmethod
    def get_price(cls, vehicle_type, package_type):
        """Lấy giá theo loại xe và gói"""
        try:
            pricing = cls.objects.get(vehicle_type=vehicle_type, package_type=package_type, is_active=True)
            return pricing.price
        except cls.DoesNotExist:
            # Giá mặc định nếu không tìm thấy
            defaults = {
                ('car', 'monthly'): 800000,
                ('motorcycle', 'monthly'): 100000,
                ('bicycle', 'monthly'): 50000,
                ('car', 'hourly'): 30000,
                ('motorcycle', 'hourly'): 5000,
                ('bicycle', 'hourly'): 0,  # Miễn phí
            }
            return defaults.get((vehicle_type, package_type), 0)