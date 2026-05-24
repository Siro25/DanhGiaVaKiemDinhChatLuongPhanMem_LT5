from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from customers.models import Customer
from vehicles.models import Vehicle
from cards.models import PaymentTransaction
import random

class Command(BaseCommand):
    help = 'Tạo dữ liệu mẫu cho khách vãng lai'
    
    def handle(self, *args, **options):
        # Tạo khách vãng lai mẫu
        guest_customers_data = [
            {'name': 'Khách A', 'phone': '0987654321'},
            {'name': 'Khách B', 'phone': '0976543210'},
            {'name': 'Khách C', 'phone': '0965432109'},
            {'name': 'Khách D', 'phone': '0954321098'},
            {'name': 'Khách E', 'phone': '0943210987'},
            {'name': 'Khách F', 'phone': '0932109876'},
            {'name': 'Khách G', 'phone': '0921098765'},
        ]
        
        created_guests = []
        for data in guest_customers_data:
            customer, created = Customer.objects.get_or_create(
                phone=data['phone'],
                defaults={
                    'name': data['name'],
                    'customer_type': 'Khách vãng lai',
                    'address': f"Địa chỉ {data['name']}"
                }
            )
            if created:
                self.stdout.write(f'Tạo khách vãng lai: {customer.name}')
            created_guests.append(customer)
        
        # Tạo xe và giao dịch cho khách vãng lai
        today = timezone.now().date()
        vehicle_types = ['car', 'motorcycle', 'bicycle']
        
        for i, customer in enumerate(created_guests):
            # Mỗi khách có 1-3 lần gửi xe
            num_visits = random.randint(1, 3)
            
            for j in range(num_visits):
                day = today - timedelta(days=random.randint(0, 30))
                plate = f"{random.choice(['51F', '59A', '60B'])}-{random.randint(100, 999)}.{random.randint(10, 99)}"
                
                # Tạo thời gian check_in trong ngày đó
                check_in_time = timezone.make_aware(
                    timezone.datetime.combine(day, timezone.datetime.min.time()) + 
                    timedelta(hours=random.randint(7, 18), minutes=random.randint(0, 59))
                )
                
                # Thời gian check_out (1-6 giờ sau check_in)
                check_out_time = check_in_time + timedelta(hours=random.randint(1, 6))
                
                vehicle, created = Vehicle.objects.get_or_create(
                    plate_number=plate,
                    defaults={
                        'vehicle_type': random.choice(vehicle_types),
                        'customer': customer,
                        'check_in': check_in_time,
                        'check_out': check_out_time,
                        'status': 'out',  # Xe vãng lai đã ra
                    }
                )
                
                if created:
                    self.stdout.write(f'Tạo xe vãng lai: {vehicle.plate_number} - {customer.name}')
                    
                    # Tạo payment transaction
                    amount = random.randint(10000, 80000)
                    payment = PaymentTransaction.objects.create(
                        vehicle=vehicle,
                        customer=customer,
                        check_in=vehicle.check_in,
                        check_out=vehicle.check_out,
                        amount=amount,
                        total=amount,
                        status='paid',
                        method=random.choice(['cash', 'card', 'momo'])
                    )
                    self.stdout.write(f'Tạo payment vãng lai: {payment.total} VNĐ')
        
        self.stdout.write(
            self.style.SUCCESS('Tạo dữ liệu khách vãng lai thành công!')
        )