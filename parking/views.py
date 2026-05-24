from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import ParkingLot, ParkingSlot, PricingSetting

def is_admin(user):
    return user.is_authenticated and user.role == "admin"

@login_required
@user_passes_test(is_admin)
def parking_dashboard(request):
    """Dashboard quản lý bãi đỗ xe"""
    parking_lots = ParkingLot.objects.all()
    total_slots = ParkingSlot.objects.count()
    available_slots = ParkingSlot.objects.filter(status="available").count()
    occupied_slots = ParkingSlot.objects.filter(status="occupied").count()
    
    # Thống kê theo loại xe
    slot_type_stats = {}
    for choice in ParkingSlot.SLOT_TYPE_CHOICES:
        slot_type = choice[0]
        slot_type_name = choice[1]
        count = ParkingSlot.objects.filter(slot_type=slot_type).count()
        slot_type_stats[slot_type_name] = count
    
    if request.user.role == "admin":
        template_name = "admin/parking/dashboard.html"
    else:
        template_name = "parking/dashboard.html"
    
    context = {
        "parking_lots": parking_lots,
        "total_slots": total_slots,
        "available_slots": available_slots,
        "occupied_slots": occupied_slots,
        "occupancy_rate": (occupied_slots / total_slots * 100) if total_slots > 0 else 0,
        "slot_type_stats": slot_type_stats,
    }
    return render(request, template_name, context)


@login_required
def pricing_list(request):
    """Hiển thị bảng giá cho nhân viên"""
    # Lấy tất cả giá đang hoạt động
    monthly_prices = PricingSetting.objects.filter(package_type='monthly', is_active=True).order_by('vehicle_type')
    hourly_prices = PricingSetting.objects.filter(package_type='hourly', is_active=True).order_by('vehicle_type')
    
    context = {
        'monthly_prices': monthly_prices,
        'hourly_prices': hourly_prices,
    }
    
    return render(request, 'parking/pricing_list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_pricing_settings(request):
    """Admin quản lý cài đặt giá"""
    if request.method == 'POST':
        # Cập nhật giá từ form
        for key, value in request.POST.items():
            if key.startswith('price_'):
                # key format: price_car_monthly
                parts = key.split('_')
                if len(parts) == 3:
                    vehicle_type = parts[1]
                    package_type = parts[2]
                    try:
                        price = float(value) if value else 0
                        PricingSetting.objects.update_or_create(
                            vehicle_type=vehicle_type,
                            package_type=package_type,
                            defaults={'price': price, 'is_active': True}
                        )
                    except (ValueError, TypeError):
                        continue
        
        messages.success(request, 'Đã cập nhật bảng giá thành công!')
        return redirect('parking:admin_pricing_settings')
    
    # Lấy tất cả cấu hình giá
    pricing_data = {}
    for vehicle_type, vehicle_name in PricingSetting.VEHICLE_TYPES:
        pricing_data[vehicle_type] = {}
        for package_type, package_name in PricingSetting.PACKAGE_TYPES:
            try:
                pricing = PricingSetting.objects.get(
                    vehicle_type=vehicle_type,
                    package_type=package_type
                )
                pricing_data[vehicle_type][package_type] = pricing.price
            except PricingSetting.DoesNotExist:
                # Sử dụng giá mặc định
                pricing_data[vehicle_type][package_type] = PricingSetting.get_price(vehicle_type, package_type)
    
    context = {
        'pricing_data': pricing_data,
        'vehicle_types': PricingSetting.VEHICLE_TYPES,
        'package_types': PricingSetting.PACKAGE_TYPES,
    }
    
    return render(request, 'admin/parking/pricing_settings.html', context)
