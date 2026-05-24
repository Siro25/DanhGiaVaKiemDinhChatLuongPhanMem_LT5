from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q, Count
from django.utils import timezone
from vehicles.models import Vehicle
from .models import Customer
try:
    from .forms import VehicleRegistrationForm
except ImportError:
    from vehicles.forms import VehicleForm as VehicleRegistrationForm


def is_khachhang(user):
	"""Kiểm tra user là khách hàng"""
	return user.is_authenticated and getattr(user, 'role', None) == 'khachhang'


def _get_customer_or_none(user):
	"""Lấy Customer profile cho user nếu có"""
	if not user.is_authenticated:
		return None
	try:
		return Customer.objects.get(user=user)
	except Customer.DoesNotExist:
		return None


def _get_or_create_customer(user):
	"""Lấy hoặc tạo Customer profile cho user"""
	if not user.is_authenticated:
		return None
	customer, created = Customer.objects.get_or_create(
		user=user,
		defaults={
			'name': user.get_full_name() or user.username,
			'phone': getattr(user, 'phone_number', ''),
			'customer_type': 'Khách vãng lai',
		}
	)
	return customer


@login_required
@user_passes_test(is_khachhang)
def dashboard(request):
	"""Dashboard dành cho khách hàng"""
	from cards.models import Notification
	from parking.models import ParkingRecord
	
	# Lấy thông báo chưa đọc
	notifications = Notification.objects.filter(user=request.user, read=False).order_by('-created_at')[:5]
	notifications_count = Notification.objects.filter(user=request.user, read=False).count()
	
	# Lấy thông tin xe
	customer = _get_customer_or_none(request.user)
	vehicles = Vehicle.objects.filter(customer=customer) if customer else Vehicle.objects.none()
	
	# Kiểm tra xe đang trong bãi
	current_parking = None
	if customer:
		# Lấy record xe đang trong bãi (chưa có exit_time)
		current_parking = ParkingRecord.objects.filter(
			vehicle__customer=customer,
			exit_time__isnull=True
		).select_related('vehicle', 'parking_lot').first()
	
	return render(request, 'customers/dashboard_user.html', {
		'notifications': notifications,
		'notifications_count': notifications_count,
		'vehicles': vehicles,
		'customer': customer,
		'current_parking': current_parking
	})

@login_required
@user_passes_test(is_khachhang)
def notifications_list(request):
	"""Danh sách tất cả thông báo"""
	from cards.models import Notification
	
	# Lấy tất cả thông báo
	all_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
	notifications_count = Notification.objects.filter(user=request.user, read=False).count()
	
	return render(request, 'customers/notifications.html', {
		'all_notifications': all_notifications,
		'notifications_count': notifications_count,
	})

@login_required
@user_passes_test(is_khachhang)
def mark_notification_read(request, pk):
	"""Đánh dấu thông báo đã đọc"""
	from cards.models import Notification
	
	notification = get_object_or_404(Notification, pk=pk, user=request.user)
	notification.read = True
	notification.save()
	
	messages.success(request, 'Đã đánh dấu thông báo đã đọc.')
	
	# Redirect về trang được chỉ định hoặc dashboard
	next_url = request.GET.get('next', 'customers:dashboard')
	return redirect(next_url)

def is_nhanvien_or_admin(user):
    """Kiểm tra user là nhân viên hoặc admin"""
    return user.is_authenticated and user.role in ['nhanvien', 'admin']

@login_required
@user_passes_test(is_nhanvien_or_admin)
def customer_list(request):
    """Hiển thị danh sách khách hàng"""
    q = request.GET.get('q', '').strip()
    customer_type_filter = request.GET.get('type', 'all')  # all, monthly, guest
    
    # Lấy tất cả khách hàng hoặc lọc theo loại
    if customer_type_filter == 'monthly':
        qs = Customer.objects.filter(customer_type='Khách gửi tháng').order_by('name')
        page_title = 'Quản lý khách hàng gửi tháng'
    elif customer_type_filter == 'guest':
        qs = Customer.objects.filter(customer_type='Khách vãng lai').order_by('name')
        page_title = 'Quản lý khách vãng lai'
    else:
        qs = Customer.objects.all().order_by('name')
        page_title = 'Quản lý tất cả khách hàng'
    
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(phone__icontains=q) |
            Q(address__icontains=q)
        ).distinct()

    # Lấy thông tin xe gần nhất cho mỗi khách hàng
    qs = qs.annotate(vehicle_count=Count('vehicles'))
    vehicles = Vehicle.objects.filter(customer__in=qs).order_by('-check_in')
    vehicle_by_customer = {}
    for v in vehicles:
        if v.customer_id not in vehicle_by_customer:
            vehicle_by_customer[v.customer_id] = v

    today = timezone.now().date()
    customers = []
    for c in qs:
        v = vehicle_by_customer.get(c.pk)
        c.latest_vehicle_plate = v.plate_number if v else None
        c.latest_vehicle_type_display = v.get_vehicle_type_display() if v else None
        
        # Thông tin subscription: lấy subscription mới nhất nếu có
        sub = c.subscriptions.order_by('-end_date').first()
        if sub:
            c.subscription_end = sub.end_date
            c.subscription_status = 'Còn hạn' if sub.end_date >= today else 'Hết hạn'
        else:
            c.subscription_end = None
            c.subscription_status = 'Chưa đăng ký'
        customers.append(c)

    return render(request, 'customers/list.html', {
        'customers': customers, 
        'q': q,
        'customer_type_filter': customer_type_filter,
        'page_title': page_title
    })

@login_required
@user_passes_test(is_nhanvien_or_admin)
def customer_detail(request, pk):
    """Xem chi tiết khách hàng"""
    customer = get_object_or_404(Customer.objects.prefetch_related('vehicles', 'subscriptions'), pk=pk)
    return render(request, 'customers/detail.html', {'customer': customer})

@login_required
@user_passes_test(is_nhanvien_or_admin)
def customer_add(request):
    """Thêm khách hàng mới (gửi tháng hoặc vãng lai)"""
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email', '')
        address = request.POST.get('address', '')
        vehicle_type = request.POST.get('vehicle_type', '')
        customer_type = request.POST.get('customer_type', 'Khách gửi tháng')  # Lấy từ form, mặc định là khách gửi tháng
        
        if name and phone:
            customer = Customer.objects.create(
                name=name,
                phone=phone,
                email=email,
                address=address,
                customer_type=customer_type,  # Sử dụng giá trị từ form
                vehicle_type=vehicle_type,
                created_by=request.user,  # Ghi lại nhân viên tạo
            )
            messages.success(request, f'Thêm {customer_type.lower()} thành công!')
            
            # Redirect về trang phù hợp với role
            if request.user.role == 'admin':
                return redirect('admin_customer_management')
            else:
                return redirect('customers:customer_list')
        else:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin!')
    
    # Chọn template dựa trên role
    if request.user.role == 'admin':
        template_name = 'admin/customers/form.html'
    else:
        template_name = 'customers/form.html'
    
    return render(request, template_name, {
        'title': 'Thêm khách hàng',
        'customer_type_fixed': False  # Cho phép chọn loại khách khi thêm mới
    })

@login_required
@user_passes_test(is_nhanvien_or_admin)
def customer_edit(request, pk):
    """Sửa thông tin khách hàng"""
    customer = get_object_or_404(Customer, pk=pk)  
    
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email', '')
        address = request.POST.get('address', '')
        vehicle_type = request.POST.get('vehicle_type', '')
        customer_type = request.POST.get('customer_type', customer.customer_type)  # Cho phép thay đổi loại khách
        
        if name and phone:
            customer.name = name
            customer.phone = phone
            customer.email = email
            customer.address = address
            customer.customer_type = customer_type  # Cập nhật loại khách
            customer.vehicle_type = vehicle_type
            customer.save()
            messages.success(request, 'Cập nhật thông tin khách hàng thành công!')
            
            # Redirect về trang phù hợp với role
            if request.user.role == 'admin':
                return redirect('admin_customer_management')
            else:
                return redirect('customers:customer_list')
        else:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin!')
    
    # Chọn template dựa trên role
    if request.user.role == 'admin':
        template_name = 'admin/customers/form.html'
    else:
        template_name = 'customers/form.html'
    
    return render(request, template_name, {
        'title': 'Sửa thông tin khách hàng', 
        'customer': customer,
        'customer_type_fixed': False  # Cho phép thay đổi loại khách
    })

@login_required
@user_passes_test(is_nhanvien_or_admin)
def customer_delete(request, pk):
    """Xóa khách hàng"""
    try:
        customer = get_object_or_404(Customer, pk=pk)  # Cho phép xóa tất cả loại khách
        
        if request.method == 'POST':
            # Kiểm tra xem khách hàng có xe đang gửi không
            vehicles_count = customer.vehicles.count()
            
            if vehicles_count > 0:
                messages.error(request, f'Không thể xóa khách hàng vì còn {vehicles_count} phương tiện liên kết. Hãy xóa tất cả phương tiện trước.')
                # Redirect về trang phù hợp với role  
                if request.user.role == 'admin':
                    return redirect('admin_customer_management')
                else:
                    return redirect('customers:customer_detail', pk=customer.pk)
            
            # Xóa các giao dịch liên quan trước khi xóa khách hàng
            from cards.models import PaymentTransaction
            related_transactions = PaymentTransaction.objects.filter(customer=customer)
            transactions_count = related_transactions.count()
            
            if transactions_count > 0:
                related_transactions.delete()
                print(f"🗑️ Deleted {transactions_count} transactions for customer {customer.name}")
            
            customer_name = customer.name
            customer.delete()
            
            # Thông báo chi tiết về việc xóa
            if transactions_count > 0:
                messages.success(request, f'Đã xóa khách hàng "{customer_name}" và {transactions_count} giao dịch liên quan thành công!')
            else:
                messages.success(request, f'Đã xóa khách hàng "{customer_name}" thành công!')
            
            # Redirect về trang phù hợp với role
            if request.user.role == 'admin':
                return redirect('admin_customer_management')
            else:
                return redirect('customers:customer_list')
        
        # GET request - show confirmation page
        context = {
            'customer': customer,
            'vehicles_count': customer.vehicles.count(),
            'page_title': 'Xóa khách hàng gửi tháng'
        }
        
        template_name = 'customers/confirmdelete.html'
        if request.user.role == 'admin':
            template_name = 'admin/customers/confirmdelete.html'
            
        return render(request, template_name, context)
        
    except Exception as e:
        messages.error(request, f'Lỗi: {str(e)}')
        # Redirect về trang phù hợp với role
        if request.user.role == 'admin':
            return redirect('admin_customer_management')
        else:
            return redirect('customers:customer_list')

# Dashboard views
@login_required
def dashboard(request):
    """Dashboard cho khách hàng"""
    from parking.models import ParkingRecord
    from cards.models import Notification
    
    if not hasattr(request.user, 'customer_profile'):
        messages.error(request, 'Bạn chưa có hồ sơ khách hàng!')
        return redirect('login')
    
    customer = request.user.customer_profile
    vehicles = customer.vehicles.all().order_by('-check_in')[:5]  # 5 xe gần nhất
    
    # Kiểm tra xe đang trong bãi
    current_parking = ParkingRecord.objects.filter(
        vehicle__customer=customer,
        exit_time__isnull=True
    ).select_related('vehicle', 'parking_lot').first()
    
    # Lấy thông báo
    notifications = Notification.objects.filter(user=request.user, read=False).order_by('-created_at')[:5]
    notifications_count = Notification.objects.filter(user=request.user, read=False).count()
    
    return render(request, 'customers/dashboard_user.html', {
        'customer': customer,
        'vehicles': vehicles,
        'current_parking': current_parking,
        'notifications': notifications,
        'notifications_count': notifications_count
    })

@login_required
def my_vehicles(request):
    """Danh sách xe của tôi"""
    if not hasattr(request.user, 'customer_profile'):
        messages.error(request, 'Bạn chưa có hồ sơ khách hàng!')
        return redirect('accounts:login')
    
    customer = request.user.customer_profile
    vehicles = customer.vehicles.all().order_by('-check_in')
    
    return render(request, 'customers/my_vehicles.html', {
        'vehicles': vehicles,
        'customer': customer
    })

@login_required
def payment_history(request):
    """Lịch sử thanh toán"""
    from django.utils import timezone
    from parking.models import PricingSetting
    from .models import Wallet, WalletTransaction
    
    if not hasattr(request.user, 'customer_profile'):
        messages.error(request, 'Bạn chưa có hồ sơ khách hàng!')
        return redirect('accounts:login')
    
    customer = request.user.customer_profile
    
    # Lấy thông tin ví
    wallet, created = Wallet.objects.get_or_create(customer=customer)
    
    # Lấy lịch sử giao dịch ví (10 giao dịch gần nhất)
    wallet_transactions = wallet.transactions.all()[:10]
    
    # Kiểm tra gói đăng ký hiện tại
    current_subscription = customer.subscriptions.filter(
        is_active=True,
        end_date__gte=timezone.now().date()
    ).first()
    
    # Lấy bảng giá từ database
    pricing = {
        'car_monthly': PricingSetting.get_price('car', 'monthly'),
        'car_hourly': PricingSetting.get_price('car', 'hourly'),
        'motorcycle_monthly': PricingSetting.get_price('motorcycle', 'monthly'),
        'motorcycle_hourly': PricingSetting.get_price('motorcycle', 'hourly'),
    }
    
    return render(request, 'customers/payment_history.html', {
        'wallet': wallet,
        'wallet_transactions': wallet_transactions,
        'customer': customer,
        'current_subscription': current_subscription,
        'pricing': pricing
    })

@login_required 
def support(request):
    """Trang hỗ trợ khách hàng"""
    return render(request, 'customers/support.html')

@login_required
def vehicle_qr(request, vehicle_id):
    """Hiển thị QR code của xe"""
    if not hasattr(request.user, 'customer_profile'):
        messages.error(request, 'Bạn chưa có hồ sơ khách hàng!')
        return redirect('accounts:login')
    
    customer = request.user.customer_profile
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id, customer=customer)
    
    return render(request, 'customers/vehicle_qr.html', {
        'vehicle': vehicle,
        'customer': customer
    })


# ============= Vehicle Management Views for Customers =============

@login_required
@user_passes_test(is_khachhang)
def vehicles_list(request):
    """Danh sách phương tiện của khách hàng"""
    from parking.models import ParkingRecord
    
    owner_obj = _get_customer_or_none(request.user)
    if owner_obj is None:
        messages.warning(request, 'Chưa tìm thấy hồ sơ khách hàng liên kết với tài khoản.')
        vehicles = Vehicle.objects.none()
    else:
        # Lấy tất cả xe của khách hàng
        vehicles = Vehicle.objects.filter(customer=owner_obj).select_related('parking_lot')
        
        # Debug: In ra số lượng xe
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Customer {owner_obj.name} has {vehicles.count()} vehicles")
        
        # Thêm thông tin trạng thái trong bãi cho mỗi xe
        for v in vehicles:
            v.in_parking = ParkingRecord.objects.filter(
                vehicle=v,
                exit_time__isnull=True
            ).exists()
    
    return render(request, 'customers/vehicles.html', {'vehicles': vehicles})


@login_required
@user_passes_test(is_khachhang)
def vehicle_register(request):
    """Đăng ký phương tiện mới"""
    owner_obj = _get_customer_or_none(request.user)
    if owner_obj is None:
        messages.error(request, 'Bạn chưa có hồ sơ khách hàng. Liên hệ quản trị.')
        return redirect('customers:dashboard')

    if request.method == 'POST':
        form = VehicleRegistrationForm(request.POST)
        if form.is_valid():
            v = form.save(commit=False)
            v.customer = owner_obj
            v.approved = False
            v.save()
            messages.success(request, 'Đăng ký phương tiện thành công. Chờ nhân viên duyệt.')
            return redirect('customers:vehicles')
    else:
        form = VehicleRegistrationForm()
    return render(request, 'customers/register_vehicle.html', {'form': form})


@login_required
@user_passes_test(is_khachhang)
def vehicle_detail(request, pk):
    """Chi tiết phương tiện"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    # kiểm tra quyền: chủ hoặc nhân viên/adm
    owner_obj = _get_customer_or_none(request.user)
    is_owner = (owner_obj is not None and vehicle.customer == owner_obj)
    if not (is_owner or request.user.role == 'nhanvien' or request.user.is_staff):
        messages.error(request, 'Bạn không có quyền xem phương tiện này.')
        return redirect('customers:vehicles')
    return render(request, 'customers/vehicle_detail.html', {'vehicle': vehicle})


@login_required
@user_passes_test(is_khachhang)
def vehicle_edit(request, pk):
    """Sửa thông tin phương tiện"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    owner_obj = _get_customer_or_none(request.user)
    is_owner = (owner_obj is not None and vehicle.customer == owner_obj)
    if not (is_owner or request.user.role == 'nhanvien' or request.user.is_staff):
        messages.error(request, 'Bạn không có quyền sửa phương tiện này.')
        return redirect('customers:vehicles')

    if request.method == 'POST':
        form = VehicleRegistrationForm(request.POST, request.FILES, instance=vehicle)
        if form.is_valid():
            # Lưu form nhưng không commit để giữ lại customer
            updated_vehicle = form.save(commit=False)
            # Đảm bảo customer không bị thay đổi
            if not updated_vehicle.customer:
                updated_vehicle.customer = owner_obj
            updated_vehicle.save()
            messages.success(request, 'Cập nhật phương tiện thành công.')
            return redirect('customers:vehicles')
    else:
        form = VehicleRegistrationForm(instance=vehicle)
    return render(request, 'customers/register_vehicle.html', {'form': form, 'vehicle': vehicle})


@login_required
@user_passes_test(is_khachhang)
def vehicle_delete(request, pk):
    """Xóa phương tiện"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    owner_obj = _get_customer_or_none(request.user)
    is_owner = (owner_obj is not None and vehicle.customer == owner_obj)
    if not (is_owner or request.user.role == 'nhanvien' or request.user.is_staff):
        messages.error(request, 'Bạn không có quyền xóa phương tiện này.')
        return redirect('customers:vehicles')

    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Xóa phương tiện thành công.')
        return redirect('customers:vehicles')
    
    return render(request, 'customers/vehicle_confirm_delete.html', {'vehicle': vehicle})


@login_required
@user_passes_test(is_nhanvien_or_admin)
def vehicle_approve(request, pk):
    """Duyệt phương tiện (chỉ nhân viên/admin)"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'POST':
        vehicle.approved = True
        vehicle.approved_by = request.user
        vehicle.handled_by = request.user
        parking_slot = request.POST.get('parking_slot', '')
        if parking_slot:
            vehicle.parking_slot = parking_slot
        vehicle.save()
        
        # Cập nhật trạng thái customer nếu cần
        if vehicle.customer:
            vehicle.customer.status = 'approved'
            vehicle.customer.save()
            
            # Tạo thông báo cho khách hàng
            if vehicle.customer.user:
                from cards.models import Notification
                Notification.objects.create(
                    user=vehicle.customer.user,
                    title=f'Xe {vehicle.plate_number} đã được duyệt',
                    message=f'Xe {vehicle.get_vehicle_type_display()} biển số {vehicle.plate_number} của bạn đã được duyệt bởi {request.user.get_full_name() or request.user.username}. '
                           f'{"Vị trí đỗ: " + parking_slot if parking_slot else "Bạn có thể sử dụng xe vào bãi đỗ."}'
                )
        
        messages.success(request, f'✅ Đã duyệt phương tiện {vehicle.plate_number}')
        
        # Redirect về trang danh sách xe chờ duyệt hoặc trang trước đó
        next_url = request.GET.get('next', '')
        if next_url:
            return redirect(next_url)
        return redirect('customers:pending_vehicles')
    
    return render(request, 'customers/vehicle_approve.html', {'vehicle': vehicle})

@login_required
@user_passes_test(is_nhanvien_or_admin)
def pending_vehicles(request):
    """Danh sách xe chờ duyệt"""
    vehicles = Vehicle.objects.filter(approved=False).select_related('customer').order_by('-created_at')
    
    return render(request, 'customers/pending_vehicles.html', {
        'vehicles': vehicles,
        'page_title': 'Danh sách xe chờ duyệt'
    })


@login_required
@user_passes_test(is_khachhang)
def payment(request, pk):
    """Thanh toán cho phương tiện"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    owner_obj = _get_customer_or_none(request.user)
    if owner_obj is None or vehicle.customer != owner_obj:
        messages.error(request, 'Không tìm thấy phương tiện.')
        return redirect('customers:vehicles')
    
    # TODO: Implement payment logic
    return render(request, 'customers/payment_detail.html', {'vehicle': vehicle})


@login_required
@user_passes_test(is_khachhang)
def history(request):
    """Lịch sử gửi xe và thanh toán"""
    from parking.models import ParkingRecord
    from django.db.models import Q
    from .models import MonthlySubscription
    
    owner_obj = _get_customer_or_none(request.user)
    if owner_obj is None:
        messages.warning(request, 'Chưa tìm thấy hồ sơ khách hàng.')
        vehicles = Vehicle.objects.none()
        payments = []
        parking_records = []
        vehicle_subscriptions = {}
    else:
        vehicles = Vehicle.objects.filter(customer=owner_obj).order_by('-check_in')
        
        # Lấy thông tin gói tháng cho từng xe
        vehicle_subscriptions = {}
        today = timezone.now().date()
        
        for vehicle in vehicles:
            # Kiểm tra xem xe có gói tháng không (dựa vào vehicle cụ thể)
            active_sub = vehicle.subscriptions.filter(
                is_active=True,
                end_date__gte=today
            ).order_by('-end_date').first()
            
            if active_sub:
                vehicle_subscriptions[vehicle.id] = {
                    'subscription': active_sub,
                    'days_left': (active_sub.end_date - today).days,
                    'is_expiring_soon': (active_sub.end_date - today).days <= 7,
                    'status': 'active'
                }
            else:
                # Kiểm tra gói đã hết hạn
                expired_sub = vehicle.subscriptions.filter(
                    end_date__lt=today
                ).order_by('-end_date').first()
                
                if expired_sub:
                    vehicle_subscriptions[vehicle.id] = {
                        'subscription': expired_sub,
                        'days_left': 0,
                        'is_expiring_soon': False,
                        'status': 'expired'
                    }
        
        # Lấy lịch sử thanh toán từ cards app nếu có
        payments = []
        
        # Lấy lịch sử ra/vào bãi
        parking_records = ParkingRecord.objects.filter(
            vehicle__customer=owner_obj
        ).select_related('vehicle', 'parking_lot').order_by('-entry_time')
    
    return render(request, 'customers/history.html', {
        'vehicles': vehicles,
        'payments': payments,
        'records': parking_records,  # Lịch sử ra/vào
        'vehicle_subscriptions': vehicle_subscriptions  # Thông tin gói tháng
    })


@login_required
@user_passes_test(is_khachhang)
def vehicle_toggle_parking(request, pk):
    """Toggle trạng thái xe vào/ra bãi"""
    from parking.models import ParkingRecord, ParkingLot
    from cards.models import Card
    from django.utils import timezone
    
    vehicle = get_object_or_404(Vehicle, pk=pk)
    owner_obj = _get_customer_or_none(request.user)
    
    # Kiểm tra quyền sở hữu
    if vehicle.customer != owner_obj:
        messages.error(request, 'Bạn không có quyền thao tác xe này.')
        return redirect('customers:vehicles')
    
    # Kiểm tra xe đã được duyệt chưa
    if not vehicle.approved:
        messages.warning(request, 'Xe chưa được duyệt, không thể vào bãi.')
        return redirect('customers:vehicles')
    
    # Kiểm tra xem xe có đang trong bãi không
    active_record = ParkingRecord.objects.filter(
        vehicle=vehicle, 
        exit_time__isnull=True
    ).first()
    
    if active_record:
        # Xe đang trong bãi -> Cho ra
        from parking.models import PricingSetting
        
        active_record.exit_time = timezone.now()
        
        # Kiểm tra xe có gói tháng không (kiểm tra theo vehicle, không phải customer)
        current_subscription = vehicle.subscriptions.filter(
            is_active=True,
            end_date__gte=timezone.now().date()
        ).first()
        
        if current_subscription:
            # Xe có gói tháng - KHÔNG tính phí
            active_record.fee = 0
            active_record.is_paid = True
            active_record.notes = f'Gói tháng: {current_subscription.start_date.strftime("%d/%m/%Y")} - {current_subscription.end_date.strftime("%d/%m/%Y")}'
            active_record.save()
            
            messages.success(request, f'✅ Xe {vehicle.plate_number} đã ra bãi. Miễn phí (Gói tháng còn {(current_subscription.end_date - timezone.now().date()).days} ngày)')
        else:
            # Khách vãng lai - Tính phí theo giờ từ bảng giá
            duration = active_record.exit_time - active_record.entry_time
            hours = max(1, duration.total_seconds() / 3600)  # Tối thiểu 1 giờ
            
            # Lấy đơn giá theo loại xe
            hourly_rate = PricingSetting.get_price(vehicle.vehicle_type, 'hourly')
            active_record.fee = int(hours * hourly_rate)
            active_record.save()
            
            messages.success(request, f'Xe {vehicle.plate_number} đã ra bãi. Phí: {active_record.fee:,.0f} VNĐ ({hours:.1f} giờ x {hourly_rate:,.0f} VNĐ)')
    else:
        # Xe chưa trong bãi -> Cho vào
        # Lấy hoặc tạo bãi xe mặc định
        parking_lot, created = ParkingLot.objects.get_or_create(
            name='Bãi xe chính',
            defaults={
                'capacity': 100,
                'available_slots': 100,
                'hourly_rate': 10000,
                'status': 'active'
            }
        )
        
        # Lấy hoặc tạo thẻ cho khách hàng
        card, _ = Card.objects.get_or_create(
            customer=owner_obj,
            defaults={
                'card_number': f'CARD-{owner_obj.id:04d}',
                'status': 'active'
            }
        )
        
        # Tạo record vào bãi
        ParkingRecord.objects.create(
            vehicle=vehicle,
            card=card,
            parking_lot=parking_lot,
            entry_time=timezone.now()
        )
        
        messages.success(request, f'Xe {vehicle.plate_number} đã vào bãi.')
    
    return redirect('customers:vehicles')
