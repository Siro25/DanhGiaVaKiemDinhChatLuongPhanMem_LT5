from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import PricingService

@login_required
def pricing_list(request):
    """Hiển thị bảng giá dịch vụ"""
    
    # Lấy bảng giá cho khách gửi tháng
    monthly_pricing = PricingService.objects.filter(
        customer_type='Khách gửi tháng',
        is_active=True
    ).order_by('vehicle_type')
    
    # Lấy bảng giá cho khách vãng lai  
    guest_pricing = PricingService.objects.filter(
        customer_type='Khách vãng lai',
        is_active=True
    ).order_by('vehicle_type')
    
    context = {
        'monthly_pricing': monthly_pricing,
        'guest_pricing': guest_pricing,
        'page_title': 'Bảng Giá Dịch Vụ'
    }
    
    return render(request, 'pricing/pricing_list.html', context)