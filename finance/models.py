from django.db import models
from django.utils.translation import gettext_lazy as _

VEHICLE_TYPE_CHOICES = [
    ('car', 'Ô tô'),
    ('motorcycle', 'Xe máy'),
    ('bicycle', 'Xe đạp'),
    ('truck', 'Xe tải'),
    ('taxi', 'Taxi'),
]

class ParkingRate(models.Model):
    vehicle_type = models.CharField(_('Loại xe'), max_length=20, choices=VEHICLE_TYPE_CHOICES)
    hourly_rate = models.DecimalField(_('Giá theo giờ'), max_digits=10, decimal_places=2)
    daily_rate = models.DecimalField(_('Giá theo ngày'), max_digits=10, decimal_places=2, null=True, blank=True)
    monthly_rate = models.DecimalField(_('Giá theo tháng'), max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Bảng giá')
        verbose_name_plural = _('Bảng giá')

    def __str__(self):
        return f"{self.get_vehicle_type_display()} - {self.hourly_rate}đ/h"