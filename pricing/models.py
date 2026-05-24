from django.db import models

class PricingService(models.Model):
    """Model quản lý bảng giá dịch vụ parking"""
    
    VEHICLE_TYPE_CHOICES = [
        ('Xe máy', 'Xe máy'),
        ('Ô tô', 'Ô tô'),
        ('Xe đạp', 'Xe đạp'),
    ]
    
    CUSTOMER_TYPE_CHOICES = [
        ('Khách gửi tháng', 'Khách gửi tháng'),
        ('Khách vãng lai', 'Khách vãng lai'),
    ]
    
    vehicle_type = models.CharField(
        max_length=20, 
        choices=VEHICLE_TYPE_CHOICES,
        verbose_name="Loại xe"
    )
    customer_type = models.CharField(
        max_length=20,
        choices=CUSTOMER_TYPE_CHOICES,
        verbose_name="Loại khách hàng"
    )
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=0,
        verbose_name="Giá (VNĐ)"
    )
    unit = models.CharField(
        max_length=20,
        default="VNĐ",
        verbose_name="Đơn vị"
    )
    duration = models.CharField(
        max_length=50,
        verbose_name="Thời gian",
        help_text="Ví dụ: /tháng, /lượt"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Đang áp dụng"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['vehicle_type', 'customer_type']
        verbose_name = "Bảng giá dịch vụ"
        verbose_name_plural = "Bảng giá dịch vụ"
        
    def __str__(self):
        return f"{self.customer_type} - {self.vehicle_type}: {self.price:,.0f} VNĐ{self.duration}"
    
    def formatted_price(self):
        """Trả về giá đã format"""
        return f"{self.price:,.0f}"
    
    @classmethod
    def get_price(cls, vehicle_type, customer_type):
        """Lấy giá cho loại xe và loại khách hàng"""
        try:
            pricing = cls.objects.get(
                vehicle_type=vehicle_type,
                customer_type=customer_type,
                is_active=True
            )
            return pricing.price
        except cls.DoesNotExist:
            return 0