from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from customers.models import Customer, MonthlySubscription
import random

class Command(BaseCommand):
    help = 'Tạo subscription cho khách gửi tháng đã có'
    
    def handle(self, *args, **options):
        # Lấy tất cả khách gửi tháng
        monthly_customers = Customer.objects.filter(customer_type='Khách gửi tháng')
        
        today = date.today()
        
        for customer in monthly_customers:
            # Kiểm tra xem đã có subscription chưa
            if not customer.subscriptions.exists():
                # Tạo subscription ngẫu nhiên
                # Một số còn hạn, một số hết hạn
                if random.choice([True, False]):
                    # Còn hạn: end_date trong tương lai
                    start_date = today - timedelta(days=random.randint(0, 30))
                    end_date = today + timedelta(days=random.randint(1, 60))
                else:
                    # Hết hạn: end_date trong quá khứ
                    start_date = today - timedelta(days=random.randint(60, 120))
                    end_date = today - timedelta(days=random.randint(1, 30))
                
                subscription = MonthlySubscription.objects.create(
                    customer=customer,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=end_date >= today
                )
                
                status = "Còn hạn" if subscription.is_active else "Hết hạn"
                self.stdout.write(f'Tạo subscription cho {customer.name}: {subscription.end_date} ({status})')
        
        self.stdout.write(
            self.style.SUCCESS('Tạo subscription thành công!')
        )