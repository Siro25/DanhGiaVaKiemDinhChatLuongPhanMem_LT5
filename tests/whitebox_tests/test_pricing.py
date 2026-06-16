"""
White-box unit tests cho chức năng Pricing (Bảng giá) - Phiên bản tối ưu.

Chỉ giữ lại 5 test cases quan trọng nhất:
✓ Tạo bảng giá thành công
✓ Giá hợp lệ vs giá không hợp lệ  
✓ Cập nhật bảng giá
✓ Tính phí theo bảng giá
✓ Quyền truy cập admin
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User
from parking.models import PricingSetting
from pricing.models import PricingService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_admin(username="admin_pricing", password="admpass!"):
    return User.objects.create_user(
        username=username, password=password,
        email=f"{username}@test.com",
        role="admin", status="approved",
    )


def make_nhanvien(username="nv_pricing", password="nvpass!"):
    return User.objects.create_user(
        username=username, password=password,
        email=f"{username}@test.com",
        role="nhanvien", status="approved",
    )


# ===========================================================================
# 5 Test Cases Chất Lượng Cao Cho Pricing
# ===========================================================================

class PricingEssentialTests(TestCase):
    """5 test cases cốt lõi cho hệ thống bảng giá."""

    def test_01_create_pricing_setting_success(self):
        """TC1: Tạo bảng giá thành công với dữ liệu hợp lệ."""
        ps = PricingSetting.objects.create(
            vehicle_type="motorcycle",
            package_type="monthly", 
            price=150000,
            is_active=True,
        )
        self.assertEqual(ps.price, 150000)
        self.assertTrue(ps.is_active)
        self.assertIn("Xe máy", str(ps))

    def test_02_price_validation_and_fallback(self):
        """TC2: Xử lý giá hợp lệ (tìm thấy) vs không hợp lệ (fallback)."""
        # Tạo giá hợp lệ
        PricingSetting.objects.create(
            vehicle_type="car",
            package_type="hourly",
            price=30000,
            is_active=True,
        )
        
        # Test tìm thấy giá
        price = PricingSetting.get_price("car", "hourly")
        self.assertEqual(price, 30000)
        
        # Test không tìm thấy → fallback
        price = PricingSetting.get_price("motorcycle", "monthly")
        self.assertEqual(price, 100000)  # Giá mặc định
        
        # Test giá = 0 (hợp lệ)
        PricingSetting.objects.create(
            vehicle_type="bicycle",
            package_type="hourly", 
            price=0,
            is_active=True,
        )
        price = PricingSetting.get_price("bicycle", "hourly")
        self.assertEqual(price, 0)

    def test_03_update_pricing_settings(self):
        """TC3: Cập nhật bảng giá thông qua admin interface."""
        self.client = Client()
        admin = make_admin()
        self.client.force_login(admin)
        
        url = reverse("parking:admin_pricing_settings")
        
        # POST để tạo/cập nhật giá
        data = {
            "price_motorcycle_hourly": "6000",
            "price_car_monthly": "900000",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        
        # Kiểm tra đã tạo thành công
        ps = PricingSetting.objects.filter(
            vehicle_type="motorcycle", 
            package_type="hourly"
        ).first()
        self.assertIsNotNone(ps)
        self.assertEqual(float(ps.price), 6000.0)

    def test_04_pricing_calculation_service(self):
        """TC4: Tính phí chính xác theo bảng giá dịch vụ."""
        # Tạo bảng giá dịch vụ
        ps = PricingService.objects.create(
            vehicle_type="Xe máy",
            customer_type="Khách gửi tháng",
            price=120000,
            unit="VNĐ",
            duration="/tháng",
            is_active=True,
        )
        
        # Test tính phí
        price = PricingService.get_price("Xe máy", "Khách gửi tháng")
        self.assertEqual(price, 120000)
        
        # Test format giá
        self.assertEqual(ps.formatted_price(), "120,000")
        
        # Test không tìm thấy → 0
        price = PricingService.get_price("Xe tải", "Khách VIP")
        self.assertEqual(price, 0)

    def test_05_admin_access_control(self):
        """TC5: Kiểm soát quyền truy cập - chỉ admin mới được quản lý giá."""
        self.client = Client()
        url = reverse("parking:admin_pricing_settings")
        
        # Test chưa đăng nhập → redirect
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        # Test nhân viên thường → từ chối
        nhanvien = make_nhanvien()
        self.client.force_login(nhanvien)
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)
        
        # Test admin → OK
        admin = make_admin()
        self.client.force_login(admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("pricing_data", response.context)
