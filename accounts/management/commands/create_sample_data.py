from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from customers.models import Customer
from vehicles.models import Vehicle
from cards.models import PaymentTransaction
from accounts.models import User
import random

class Command(BaseCommand):
    help = 'Tạo dữ liệu mẫu cho dashboard'
    
    def handle(self, *args, **options):
        # Tạo khách hàng mẫu
        customers_data = [
            {'name': 'Nguyễn Văn A', 'phone': '0901234567', 'customer_type': 'Khách vãng lai'},
            {'name': 'Trần Thị B', 'phone': '0912345678', 'customer_type': 'Khách gửi tháng'},
            {'name': 'Lê Văn C', 'phone': '0923456789', 'customer_type': 'Khách gửi tháng'},
            {'name': 'Phạm Thị D', 'phone': '0934567890', 'customer_type': 'Khách vãng lai'},
            {'name': 'Hoàng Văn E', 'phone': '0945678901', 'customer_type': 'Khách gửi tháng'},
        ]
        
        created_customers = []
        for data in customers_data:
            customer, created = Customer.objects.get_or_create(
                phone=data['phone'],
                defaults=data
            )
            if created:
                self.stdout.write(f'Tạo khách hàng: {customer.name}')
            created_customers.append(customer)
        
        # Tạo dữ liệu xe cho 7 ngày gần đây
        today = timezone.now().date()
        vehicle_types = ['car', 'motorcycle', 'bicycle']
        
        for i in range(7):
            day = today - timedelta(days=i)
            num_vehicles = random.randint(1, 5)
            
            for j in range(num_vehicles):
                customer = random.choice(created_customers)
                plate = f"{random.choice(['29A', '30A', '51B'])}-{random.randint(100, 999)}.{random.randint(10, 99)}"
                
                # Tạo thời gian check_in trong ngày đó
                check_in_time = timezone.make_aware(
                    timezone.datetime.combine(day, timezone.datetime.min.time()) + 
                    timedelta(hours=random.randint(7, 18), minutes=random.randint(0, 59))
                )
                
                vehicle, created = Vehicle.objects.get_or_create(
                    plate_number=plate,
                    defaults={
                        'vehicle_type': random.choice(vehicle_types),
                        'customer': customer,
                        'check_in': check_in_time,
                        'status': 'out' if i > 2 else random.choice(['in', 'out']),
                    }
                )
                
                if created:
                    # Nếu xe đã ra thì set thời gian check_out
                    if vehicle.status == 'out':
                        vehicle.check_out = check_in_time + timedelta(hours=random.randint(1, 8))
                        vehicle.save()
                    
                    self.stdout.write(f'Tạo xe: {vehicle.plate_number} - {day}')
                    
                    # Tạo payment transaction cho xe đã ra
                    if vehicle.status == 'out':
                        payment = PaymentTransaction.objects.create(
                            vehicle=vehicle,
                            customer=customer,
                            check_in=vehicle.check_in,
                            check_out=vehicle.check_out,
                            amount=random.randint(10000, 50000),
                            total=random.randint(10000, 50000),
                            status='paid',
                            method='cash'
                        )
                        self.stdout.write(f'Tạo payment: {payment.total} VNĐ')
        
        self.stdout.write(
            self.style.SUCCESS('Tạo dữ liệu mẫu thành công!')
        )