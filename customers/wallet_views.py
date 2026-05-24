"""
Views xử lý ví điện tử
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from .models import Customer, Wallet, WalletTransaction


@login_required
def wallet_view(request):
    """Hiển thị ví và lịch sử giao dịch"""
    from parking.models import ParkingRecord
    
    if not hasattr(request.user, 'customer_profile'):
        messages.error(request, 'Bạn chưa có hồ sơ khách hàng!')
        return redirect('login')
    
    customer = request.user.customer_profile
    
    # Tạo ví nếu chưa có
    wallet, created = Wallet.objects.get_or_create(customer=customer)
    
    # Lấy lịch sử giao dịch
    transactions = wallet.transactions.all()[:20]  # 20 giao dịch gần nhất
    
    # Tính tổng tiền nợ (các lần gửi xe chưa thanh toán)
    unpaid_records = ParkingRecord.objects.filter(
        vehicle__customer=customer,
        is_paid=False,
        exit_time__isnull=False  # Đã ra bãi nhưng chưa thanh toán
    )
    total_debt = sum(record.fee for record in unpaid_records)
    
    return render(request, 'customers/wallet.html', {
        'customer': customer,
        'wallet': wallet,
        'transactions': transactions,
        'total_debt': total_debt,
        'unpaid_records': unpaid_records
    })


@login_required
def wallet_deposit(request):
    """Nạp tiền vào ví"""
    if not hasattr(request.user, 'customer_profile'):
        messages.error(request, 'Bạn chưa có hồ sơ khách hàng!')
        return redirect('login')
    
    customer = request.user.customer_profile
    wallet, created = Wallet.objects.get_or_create(customer=customer)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method', 'bank_transfer')
        
        try:
            amount = Decimal(amount)
            if amount <= 0:
                messages.error(request, 'Số tiền phải lớn hơn 0!')
                return redirect('customers:wallet_deposit')
            
            # Tạo giao dịch nạp tiền
            with transaction.atomic():
                balance_before = wallet.balance
                wallet.balance += amount
                wallet.save()
                
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='deposit',
                    amount=amount,
                    balance_before=balance_before,
                    balance_after=wallet.balance,
                    status='completed',
                    description=f'Nạp tiền qua {payment_method}'
                )
            
            messages.success(request, f'Nạp {amount:,.0f} VNĐ thành công! Số dư hiện tại: {wallet.balance:,.0f} VNĐ')
            return redirect('customers:wallet')
            
        except (ValueError, TypeError):
            messages.error(request, 'Số tiền không hợp lệ!')
            return redirect('customers:wallet_deposit')
    
    # GET request
    return render(request, 'customers/wallet_deposit.html', {
        'customer': customer,
        'wallet': wallet
    })


@login_required
def wallet_payment(request, amount):
    """Thanh toán bằng ví (gọi từ subscription)"""
    if not hasattr(request.user, 'customer_profile'):
        return False
    
    customer = request.user.customer_profile
    wallet, created = Wallet.objects.get_or_create(customer=customer)
    
    amount = Decimal(amount)
    
    if wallet.balance < amount:
        return False
    
    # Trừ tiền trong ví
    with transaction.atomic():
        balance_before = wallet.balance
        wallet.balance -= amount
        wallet.save()
        
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='payment',
            amount=amount,
            balance_before=balance_before,
            balance_after=wallet.balance,
            status='completed',
            description='Thanh toán gói đăng ký tháng'
        )
    
    return True


@login_required
def pay_debt(request, record_id):
    """Thanh toán một khoản nợ (parking record)"""
    from parking.models import ParkingRecord
    from cards.models import PaymentTransaction
    from django.shortcuts import get_object_or_404
    
    if request.method != 'POST':
        messages.error(request, 'Phương thức không hợp lệ!')
        return redirect('customers:wallet')
    
    if not hasattr(request.user, 'customer_profile'):
        messages.error(request, 'Bạn chưa có hồ sơ khách hàng!')
        return redirect('login')
    
    customer = request.user.customer_profile
    wallet, created = Wallet.objects.get_or_create(customer=customer)
    
    # Lấy parking record
    record = get_object_or_404(ParkingRecord, id=record_id, vehicle__customer=customer, is_paid=False)
    
    # Kiểm tra số dư
    if wallet.balance < record.fee:
        messages.error(request, f'Số dư không đủ! Cần {record.fee:,.0f} VNĐ, hiện có {wallet.balance:,.0f} VNĐ')
        return redirect('customers:wallet')
    
    # Thanh toán
    try:
        with transaction.atomic():
            balance_before = wallet.balance
            wallet.balance -= record.fee
            wallet.save()
            
            # Đánh dấu đã thanh toán
            record.is_paid = True
            record.save()
            
            # Tạo giao dịch ví
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='payment',
                amount=record.fee,
                balance_before=balance_before,
                balance_after=wallet.balance,
                status='completed',
                description=f'Thanh toán phí gửi xe {record.vehicle.plate_number} - {record.parking_lot.name}'
            )
            
            # TẠO PAYMENT TRANSACTION ĐỂ TÍNH VÀO DOANH THU
            PaymentTransaction.objects.create(
                vehicle=record.vehicle,
                customer=customer,
                check_in=record.entry_time,
                check_out=record.exit_time,
                amount=record.fee,
                tax=Decimal('0'),
                total=record.fee,
                status='paid',
                method='wallet',
                reference=f'Wallet payment for parking record #{record.id}',
                created_by=request.user
            )
        
        messages.success(request, f'Đã thanh toán {record.fee:,.0f} VNĐ cho xe {record.vehicle.plate_number}. Số dư còn lại: {wallet.balance:,.0f} VNĐ')
    except Exception as e:
        messages.error(request, f'Lỗi thanh toán: {str(e)}')
    
    return redirect('customers:wallet')


@login_required
def pay_all_debt(request):
    """Thanh toán tất cả các khoản nợ"""
    from parking.models import ParkingRecord
    from cards.models import PaymentTransaction
    
    if request.method != 'POST':
        messages.error(request, 'Phương thức không hợp lệ!')
        return redirect('customers:wallet')
    
    if not hasattr(request.user, 'customer_profile'):
        messages.error(request, 'Bạn chưa có hồ sơ khách hàng!')
        return redirect('login')
    
    customer = request.user.customer_profile
    wallet, created = Wallet.objects.get_or_create(customer=customer)
    
    # Lấy tất cả các khoản nợ
    unpaid_records = ParkingRecord.objects.filter(
        vehicle__customer=customer,
        is_paid=False,
        exit_time__isnull=False
    )
    
    if not unpaid_records.exists():
        messages.info(request, 'Không có khoản nợ nào cần thanh toán!')
        return redirect('customers:wallet')
    
    total_debt = sum(record.fee for record in unpaid_records)
    
    # Kiểm tra số dư
    if wallet.balance < total_debt:
        messages.error(request, f'Số dư không đủ! Cần {total_debt:,.0f} VNĐ, hiện có {wallet.balance:,.0f} VNĐ')
        return redirect('customers:wallet')
    
    # Thanh toán tất cả
    try:
        with transaction.atomic():
            balance_before = wallet.balance
            wallet.balance -= total_debt
            wallet.save()
            
            # Đánh dấu tất cả đã thanh toán và tạo PaymentTransaction cho mỗi record
            count = unpaid_records.count()
            for record in unpaid_records:
                record.is_paid = True
                record.save()
                
                # TẠO PAYMENT TRANSACTION ĐỂ TÍNH VÀO DOANH THU
                PaymentTransaction.objects.create(
                    vehicle=record.vehicle,
                    customer=customer,
                    check_in=record.entry_time,
                    check_out=record.exit_time,
                    amount=record.fee,
                    tax=Decimal('0'),
                    total=record.fee,
                    status='paid',
                    method='wallet',
                    reference=f'Wallet payment for parking record #{record.id}',
                    created_by=request.user
                )
            
            # Tạo giao dịch ví (1 giao dịch tổng)
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='payment',
                amount=total_debt,
                balance_before=balance_before,
                balance_after=wallet.balance,
                status='completed',
                description=f'Thanh toán tất cả {count} khoản phí gửi xe'
            )
        
        messages.success(request, f'Đã thanh toán tất cả {count} khoản nợ ({total_debt:,.0f} VNĐ). Số dư còn lại: {wallet.balance:,.0f} VNĐ')
    except Exception as e:
        messages.error(request, f'Lỗi thanh toán: {str(e)}')
    
    return redirect('customers:wallet')
