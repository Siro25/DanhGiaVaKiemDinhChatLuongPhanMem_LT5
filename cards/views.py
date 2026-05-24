from django.shortcuts import render, get_object_or_404, redirect
from .models import PaymentTransaction
from .utils import rate_by_hour
from vehicles.models import Vehicle
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import resolve_url
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q, Sum
from .forms import PaymentFilterForm
import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from customers.models import Customer
from django.core.exceptions import FieldError
from django.core.paginator import Paginator

# View mới để quản lý khách vãng lai
@login_required
def guest_customer_list(request):
    """Danh sách khách vãng lai - sẽ liên kết với phần user"""
    q = request.GET.get('q', '').strip()
    # Chỉ hiển thị khách vãng lai
    qs = Customer.objects.filter(customer_type='Khách vãng lai').order_by('-created_at')
    
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(phone__icontains=q) |
            Q(license_plate__icontains=q)
        ).distinct()

    # Phân trang
    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Lấy xe gần nhất cho mỗi khách
    vehicles = Vehicle.objects.filter(customer__in=qs).order_by('-id')
    vehicle_by_customer = {}
    for v in vehicles:
        if v.customer_id not in vehicle_by_customer:
            vehicle_by_customer[v.customer_id] = v

    customers = []
    for c in page_obj:
        v = vehicle_by_customer.get(c.pk)
        c.latest_vehicle_plate = v.plate_number if v else None
        c.latest_vehicle_type_display = v.get_vehicle_type_display() if v else None
        c.latest_payment_total = PaymentTransaction.objects.filter(
            customer=c, status='paid'
        ).last()
        customers.append(c)

    return render(request, 'cards/guest_customer_list.html', {
        'customers': customers,
        'page_obj': page_obj,
        'q': q,
        'page_title': 'Quản lý khách vãng lai'
    })

@login_required
def guest_customer_vehicles(request, customer_id):
    """Danh sách xe của khách vãng lai cụ thể"""
    customer = get_object_or_404(Customer, pk=customer_id, customer_type='Khách vãng lai')
    vehicles = Vehicle.objects.filter(customer=customer).order_by('-check_in')
    
    # Tính tổng chi tiêu
    total_spent = PaymentTransaction.objects.filter(
        customer=customer, status='paid'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    return render(request, 'cards/guest_customer_vehicles.html', {
        'customer': customer,
        'vehicles': vehicles,
        'total_spent': total_spent,
        'page_title': f'Lịch sử xe - {customer.name}'
    })

@login_required
def payment_list(request):
    """Danh sách thanh toán cho khách vãng lai + Logic tự động tạo từ vehicle hoặc customer"""
    
    # === LOGIC TỰ ĐỘNG TẠO PAYMENT ===
    vehicle_id = request.GET.get('vehicle')
    customer_id = request.GET.get('customer')
    action = request.GET.get('action')
    
    if action == 'create':
        # Từ vehicle
        if vehicle_id:
            try:
                # try to fetch vehicle by PK first, then check status so we can give clearer messages
                vehicle = Vehicle.objects.select_related('customer').get(pk=vehicle_id)
                if vehicle.status != 'in':
                    messages.error(request, f"Xe {vehicle.plate_number} không đang gửi (trạng thái: {vehicle.get_status_display()}). Không tạo đơn.")
                    return redirect('cards:payment_list')
                
                existing = PaymentTransaction.objects.filter(vehicle=vehicle, status__in=['pending', 'paid']).first()
                if existing:
                    messages.warning(request, f'Xe {vehicle.plate_number} đã có đơn #{existing.pk}')
                else:
                    # Chỉ tạo transaction thủ công cho khách vãng lai
                    # Khách gửi tháng sẽ được tạo tự động qua signal khi thêm xe
                    if vehicle.customer.customer_type == 'Khách vãng lai':
                        now = timezone.now()
                        payment = PaymentTransaction.objects.create(
                            customer=vehicle.customer,
                            vehicle=vehicle,
                            check_in=vehicle.check_in,
                            check_out=now,
                            method='cash',
                            reference='',
                            created_by=request.user,  # Ghi lại người tạo
                        )
                        # calculate totals (uses models.PaymentTransaction.calculate)
                        try:
                            payment.calculate(rate_by_hour)
                            payment.save()
                        except Exception:
                            # fallback: set amount via helper if calculate fails
                            payment.amount = calculate_parking_fee(vehicle)
                            payment.total = payment.amount
                            payment.save()
                        messages.success(request, f'Đã tạo đơn #{payment.pk} - {payment.total} VNĐ')
                    else:
                        messages.info(request, f'Giao dịch cho khách gửi tháng sẽ được tạo tự động khi thêm xe')
                
                return redirect('cards:payment_list')
            except Vehicle.DoesNotExist:
                messages.error(request, 'Xe không tồn tại')
                return redirect('cards:payment_list')
        
        # Từ customer
        elif customer_id:
            try:
                customer = Customer.objects.get(pk=customer_id)
                vehicle = Vehicle.objects.filter(customer=customer, status='in').order_by('-check_in').first()
                
                if not vehicle:
                    messages.error(request, f'{customer.name} không có xe đang gửi')
                    return redirect('cards:payment_list')
                
                existing = PaymentTransaction.objects.filter(vehicle=vehicle, status__in=['pending', 'paid']).first()
                if existing:
                    messages.warning(request, f'Xe {vehicle.plate_number} đã có đơn #{existing.pk}')
                else:
                    # Chỉ tạo transaction thủ công cho khách vãng lai  
                    # Khách gửi tháng sẽ được tạo tự động qua signal khi thêm xe
                    if customer.customer_type == 'Khách vãng lai':
                        now = timezone.now()
                        payment = PaymentTransaction.objects.create(
                            customer=customer,
                            vehicle=vehicle,
                            check_in=vehicle.check_in,
                            check_out=now,
                            method='cash',
                            reference='',
                            created_by=request.user,  # Ghi lại người tạo
                        )
                        try:
                            payment.calculate(rate_by_hour)
                            payment.save()
                        except Exception:
                            payment.amount = calculate_parking_fee(vehicle)
                            payment.total = payment.amount
                            payment.save()
                        messages.success(request, f'Đã tạo đơn #{payment.pk} - {payment.total} VNĐ')
                    else:
                        messages.info(request, f'Giao dịch cho khách gửi tháng sẽ được tạo tự động khi thêm xe')
                
                return redirect('cards:payment_list')
            except Customer.DoesNotExist:
                messages.error(request, 'Khách hàng không tồn tại')
                return redirect('cards:payment_list')
    
    form = PaymentFilterForm(request.GET or None)
    # Chỉ hiển thị thanh toán của khách vãng lai
    qs = PaymentTransaction.objects.filter(
        customer__customer_type='Khách vãng lai'
    ).order_by('-created_at')

    q = request.GET.get('q','').strip()
    status = None
    method = None
    date_from = None
    date_to = None

    if form.is_valid():
        q = form.cleaned_data.get('q','').strip() or q
        status = form.cleaned_data.get('status')
        method = form.cleaned_data.get('method')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')

    if q:
        qs = qs.filter(Q(vehicle__plate_number__icontains=q)|Q(customer__name__icontains=q))
    if status:
        qs = qs.filter(status=status)
    if method:
        qs = qs.filter(method=method)
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    today = timezone.now().date()
    try:
        today_total = PaymentTransaction.objects.filter(
            created_at__date=today, 
            status='paid',
            customer__customer_type='Khách vãng lai'
        ).aggregate(total=Sum('total'))['total'] or 0
    except FieldError:
        today_total = 0

    return render(request, 'cards/payments_list.html', {
        'payments': qs, 
        'form': form, 
        'today_total': today_total,
        'page_title': 'Quản lý thu phí (Khách vãng lai)'
    })

def payment_detail(request, pk):
    p = get_object_or_404(PaymentTransaction, pk=pk)
    is_admin = getattr(request.user, 'role', None) == 'admin' or getattr(request.user, 'is_superuser', False)
    template = 'admin/cards/payment_detail.html' if is_admin else 'cards/payment_detail.html'
    return render(request, template, {'payment': p})

def create_from_vehicle(request, vehicle_pk):
    # Legacy endpoint kept for backward compatibility with old templates/links.
    # Redirect to the unified payment_list handler which will create the payment
    # when called with ?vehicle=<pk>&action=create
    return redirect(f"{reverse('cards:payment_list')}?vehicle={vehicle_pk}&action=create")

@require_POST
def mark_paid(request, pk):
    p = get_object_or_404(PaymentTransaction, pk=pk)
    p.status = 'paid'
    p.method = request.POST.get('method','cash')
    p.reference = request.POST.get('reference','')
    p.save()
    if p.vehicle:
        p.vehicle.status = 'out'
        p.vehicle.check_out = p.check_out
        p.vehicle.save()

    # tạo thông báo in-app (nếu model Notification tồn tại)
    try:
        # gửi thông báo cho tất cả staff (có thể thay logic gửi cho cashier)
        User = get_user_model()
        staff_qs = User.objects.filter(is_staff=True)
        from .models import Notification
        for u in staff_qs:
            Notification.objects.create(user=u, title=f"Thanh toán #{p.pk}", message=f"Thanh toán {p.total} đã được xác nhận.")
    except Exception:
        # bỏ qua nếu model chưa có / lỗi
        pass

    # Django messages để hiện toast / flash message
    messages.success(request, f"Thanh toán #{p.pk} đã được đánh dấu là Đã thanh toán.")

    # redirect an toàn: ưu tiên param next, fallback về vehicles list
    next_url = request.POST.get('next') or request.GET.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    
    # Check user role for appropriate redirect
    if hasattr(request.user, 'role') and request.user.role == 'admin':
        return redirect('admin_payment_management')
    else:
        # nếu muốn quay về danh sách phương tiện mặc định
        return redirect(resolve_url('vehicles:vehicle_list'))

@require_POST
def cancel_payment(request, pk):
    p = get_object_or_404(PaymentTransaction, pk=pk)
    if p.status == 'paid':
        messages.error(request, "Không thể hủy giao dịch đã thanh toán.")
    else:
        p.status = 'cancelled'
        p.save()
        messages.success(request, f"Giao dịch #{p.pk} đã bị hủy.")
    return redirect('cards:payment_list')

def payments_alias(request):
    return redirect('cards:payment_list')

def export_payments_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payments.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID','Phương tiện','Khách','Tổng','Trạng thái','Ngày tạo'])
    qs = PaymentTransaction.objects.all().order_by('-created_at')
    for p in qs:
        writer.writerow([p.pk, p.vehicle.plate_number if p.vehicle else '', p.customer.name if p.customer else '', p.total, p.get_status_display(), p.created_at])
    return response

def calculate_parking_fee(vehicle):
    """Hàm tính phí đỗ xe"""
    if not vehicle.check_in:
        return 5000
    
    hours = (timezone.now() - vehicle.check_in).total_seconds() / 3600
    rates = {'bicycle': 3000, 'motorcycle': 5000, 'car': 10000}
    rate = rates.get(vehicle.vehicle_type, 5000)
    amount = int(hours * rate)
    amount = ((amount + 999) // 1000) * 1000
    return amount if amount > 0 else 5000

@login_required
def guest_checkin(request):
    """Check-in cho khách vãng lai - Thêm tin"""
    from .forms import GuestCheckinForm
    
    if request.method == 'POST':
        form = GuestCheckinForm(request.POST, request.FILES)
        if form.is_valid():
            # Lấy hoặc tạo khách hàng
            phone = form.cleaned_data['phone']
            name = form.cleaned_data['name']
            
            customer, created = Customer.objects.get_or_create(
                phone=phone,
                customer_type='Khách vãng lai',
                defaults={
                    'name': name,
                    'created_by': request.user
                }
            )
            
            # Nếu khách hàng đã tồn tại, cập nhật tên (nếu khác)
            if not created and customer.name != name:
                customer.name = name
                customer.save()
            
            # Tạo vehicle mới
            vehicle = Vehicle.objects.create(
                plate_number=form.cleaned_data['plate_number'],
                vehicle_type=form.cleaned_data['vehicle_type'],
                color=form.cleaned_data.get('color', ''),
                customer=customer,
                service_package='guest',
                status='in',
                created_by=request.user,
                handled_by=request.user,
                image=form.cleaned_data.get('image')
            )
            
            # Tạo payment transaction
            from pricing.models import PricingService
            try:
                pricing = PricingService.objects.get(
                    vehicle_type=vehicle.get_vehicle_type_display(),
                    customer_type='Khách vãng lai',
                    is_active=True
                )
                amount = pricing.price
            except PricingService.DoesNotExist:
                # Default prices
                default_prices = {
                    'motorcycle': 5000,
                    'car': 10000,
                    'bicycle': 3000
                }
                amount = default_prices.get(vehicle.vehicle_type, 5000)
            
            transaction = PaymentTransaction.objects.create(
                customer=customer,
                vehicle=vehicle,
                check_in=vehicle.check_in,
                amount=amount,
                total=amount,
                method='cash',
                status='pending',
                reference=f'GUEST-{vehicle.id}-{timezone.now().strftime("%Y%m%d%H%M%S")}',
                created_by=request.user
            )
            
            messages.success(request, f'✅ Đã check-in xe {vehicle.plate_number} cho khách {customer.name}. Phí dự kiến: {amount:,.0f} VNĐ')
            return redirect('cards:payment_detail', pk=transaction.pk)
    else:
        form = GuestCheckinForm()
    
    return render(request, 'cards/guest_checkin.html', {
        'form': form,
        'page_title': 'Check-in khách vãng lai'
    })