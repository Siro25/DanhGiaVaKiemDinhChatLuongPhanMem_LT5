from django.core.management.base import BaseCommand
from parking.models import PricingSetting

class Command(BaseCommand):
    help = 'Khởi tạo bảng giá mặc định'

    def handle(self, *args, **options):
        # Dữ liệu giá mặc định
        prices = [
            # Vé tháng
            ('car', 'monthly', 800000),
            ('motorcycle', 'monthly', 100000),
            ('bicycle', 'monthly', 50000),
            # Vé theo lượt
            ('car', 'hourly', 30000),
            ('motorcycle', 'hourly', 5000),
            ('bicycle', 'hourly', 0),  # Miễn phí
        ]
        
        for vehicle_type, package_type, price in prices:
            pricing, created = PricingSetting.objects.get_or_create(
                vehicle_type=vehicle_type,
                package_type=package_type,
                defaults={
                    'price': price,
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Đã tạo giá: {pricing.get_vehicle_type_display()} - {pricing.get_package_type_display()}: {pricing.price:,.0f} VNĐ'
                    )
                )
            else:
                self.stdout.write(
                    f'Giá đã tồn tại: {pricing.get_vehicle_type_display()} - {pricing.get_package_type_display()}: {pricing.price:,.0f} VNĐ'
                )
        
        self.stdout.write(
            self.style.SUCCESS('Hoàn thành khởi tạo bảng giá!')
        )