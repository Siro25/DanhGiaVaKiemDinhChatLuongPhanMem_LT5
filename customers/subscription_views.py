"""
Views xử lý đăng ký và gia hạn gói tháng
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction as db_transaction
from datetime import timedelta
from decimal import Decimal
from .models import Customer, MonthlySubscription, Wallet, WalletTransaction
from parking.models import PricingSetting


@login_required
def subscribe_monthly(request):
    """Đăng ký gói tháng mới hoặc gia hạn"""
    if not hasattr(request.user, 'customer_profile'):
        messages.error(request, 'Bạn chưa có hồ sơ khách hàng!')
        return redirect('login')
    
    customer = request.user.customer_profile
    
    if request.method == 'POST':
        from vehicles.models import Vehicle
        
        vehicle_id = request.POST.get('vehicle_id')
        vehicle_type = request.POST.get('vehicle_type', 'car')
        duration_months = int(request.POST.get('duration', 1))
        payment_method = request.POST.get('payment_method', 'wallet')
        
        # Lấy xe được chọn nếu có
        vehicle = None
        if vehicle_id:
            try:
                vehicle = Vehicle.objects.get(id=vehicle_id, customer=customer)
                vehicle_type = vehicle.vehicle_type  # Lấy loại xe từ vehicle object
            except Vehicle.DoesNotExist:
                messages.error(request, 'Xe không tồn tại!')
                return redirect('customers:subscribe_monthly')
        
        # Lấy giá từ database
        monthly_price = PricingSetting.get_price(vehicle_type, 'monthly')
        total_amount = Decimal(monthly_price * duration_months)
        
        # Kiểm tra ví
        wallet, created = Wallet.objects.get_or_create(customer=customer)
        
        if payment_method == 'wallet':
            if wallet.balance < total_amount:
                messages.error(
                    request, 
                    f'Số dư ví không đủ! Cần {total_amount:,.0f} VNĐ, hiện có {wallet.balance:,.0f} VNĐ. '
                    f'Vui lòng nạp thêm {(total_amount - wallet.balance):,.0f} VNĐ.'
                )
                return redirect('customers:wallet_deposit')
        
        # Tính ngày bắt đầu và kết thúc
        # Luôn bắt đầu từ hôm nay
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=30 * duration_months)
        
        # Thực hiện thanh toán và tạo subscription
        try:
            with db_transaction.atomic():
                # Vô hiệu hóa gói cũ của xe này nếu có
                if vehicle:
                    old_subs = vehicle.subscriptions.filter(
                        is_active=True,
                        end_date__gte=timezone.now().date()
                    )
                    if old_subs.exists():
                        old_subs.update(is_active=False)
                
                # Trừ tiền từ ví
                if payment_method == 'wallet':
                    balance_before = wallet.balance
                    wallet.balance -= total_amount
                    wallet.save()
                    
                    # Tạo giao dịch ví
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='payment',
                        amount=total_amount,
                        balance_before=balance_before,
                        balance_after=wallet.balance,
                        status='completed',
                        description=f'Thanh toán gói {duration_months} tháng - {vehicle.plate_number if vehicle else vehicle_type}'
                    )
                    
                    # TẠO PAYMENT TRANSACTION ĐỂ TÍNH VÀO DOANH THU
                    from cards.models import PaymentTransaction
                    PaymentTransaction.objects.create(
                        customer=customer,
                        check_in=timezone.now(),
                        check_out=timezone.now(),
                        amount=total_amount,
                        tax=Decimal('0'),
                        total=total_amount,
                        status='paid',
                        method='wallet',
                        reference=f'Monthly subscription {duration_months} months - {vehicle.plate_number if vehicle else vehicle_type}',
                        created_by=request.user
                    )
                
                # Tạo subscription mới cho xe cụ thể
                subscription = MonthlySubscription.objects.create(
                    customer=customer,
                    vehicle=vehicle,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=True
                )
                
                # Cập nhật customer type
                if customer.customer_type != 'Khách gửi tháng':
                    customer.customer_type = 'Khách gửi tháng'
                    customer.save()
            
            messages.success(
                request, 
                f'✅ Đăng ký gói tháng thành công! '
                f'Xe: {vehicle.plate_number if vehicle else "N/A"}. '
                f'Từ {start_date.strftime("%d/%m/%Y")} đến {end_date.strftime("%d/%m/%Y")}. '
                f'Đã thanh toán: {total_amount:,.0f} VNĐ. '
                f'Số dư còn lại: {wallet.balance:,.0f} VNĐ'
            )
            return redirect('customers:payment_history')
            
        except Exception as e:
            messages.error(request, f'Có lỗi xảy ra: {str(e)}')
            return redirect('customers:subscribe_monthly')
    
    # GET request - hiển thị form
    from vehicles.models import Vehicle
    
    # Lấy danh sách xe của khách hàng
    customer_vehicles = Vehicle.objects.filter(
        customer=customer,
        approved=True
    ).order_by('-created_at')
    
    # Lấy bảng giá
    pricing = {
        'car_monthly': PricingSetting.get_price('car', 'monthly'),
        'motorcycle_monthly': PricingSetting.get_price('motorcycle', 'monthly'),
        'bicycle_monthly': PricingSetting.get_price('bicycle', 'monthly'),
    }
    
    # Kiểm tra gói hiện tại
    current_subscription = customer.subscriptions.filter(
        is_active=True,
        end_date__gte=timezone.now().date()
    ).first()
    
    # Lấy thông tin ví
    wallet, created = Wallet.objects.get_or_create(customer=customer)
    
    return render(request, 'customers/subscribe_monthly.html', {
        'customer': customer,
        'customer_vehicles': customer_vehicles,
        'pricing': pricing,
        'current_subscription': current_subscription,
        'wallet': wallet
    })
