"""
White-box unit tests cho chức năng Pricing (Bảng giá).

Dựa trên phân tích source code:
  - parking/models.py : PricingSetting (get_price, VEHICLE_TYPES, PACKAGE_TYPES)
  - parking/views.py  : pricing_list, admin_pricing_settings
  - pricing/models.py : PricingService (get_price, formatted_price)

Mục tiêu phủ:
  Statement Coverage  – mọi câu lệnh được thực thi.
  Branch Coverage     – các nhánh: tìm thấy / không tìm thấy / inactive setting.
  Condition Coverage  – mọi điều kiện: is_active=True/False, DoesNotExist.

Hai model pricing tồn tại song song:
  1. parking.PricingSetting  – bảng giá chính (theo loại xe + gói)
  2. pricing.PricingService  – bảng giá dịch vụ (theo loại khách + loại xe)
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
# Tests cho PricingSetting (parking app)
# ===========================================================================

class PricingSettingModelTests(TestCase):
    """Kiểm tra parking/models.py::PricingSetting."""

    def test_create_pricing_setting(self):
        """Tạo PricingSetting thành công."""
        ps = PricingSetting.objects.create(
            vehicle_type="motorcycle",
            package_type="monthly",
            price=150000,
            is_active=True,
        )
        self.assertEqual(ps.price, 150000)
        self.assertTrue(ps.is_active)

    def test_str_representation(self):
        """__str__ chứa loại xe, gói và giá."""
        ps = PricingSetting.objects.create(
            vehicle_type="car",
            package_type="hourly",
            price=30000,
            is_active=True,
        )
        s = str(ps)
        self.assertIn("Ô tô", s)
        self.assertIn("30,000", s)

    def test_unique_together_vehicle_package(self):
        """(vehicle_type, package_type) phải duy nhất."""
        from django.db import IntegrityError
        PricingSetting.objects.create(
            vehicle_type="bicycle",
            package_type="hourly",
            price=0,
            is_active=True,
        )
        with self.assertRaises(IntegrityError):
            PricingSetting.objects.create(
                vehicle_type="bicycle",
                package_type="hourly",
                price=1000,
                is_active=True,
            )

    # --- get_price: branch tìm thấy ----------------------------------------

    def test_get_price_found_active(self):
        """get_price() trả về giá khi tìm thấy setting active."""
        PricingSetting.objects.create(
            vehicle_type="motorcycle",
            package_type="hourly",
            price=5000,
            is_active=True,
        )
        price = PricingSetting.get_price("motorcycle", "hourly")
        self.assertEqual(price, 5000)

    # --- get_price: branch không tìm thấy (DoesNotExist) -------------------

    def test_get_price_not_found_returns_default_motorcycle_hourly(self):
        """Không tìm thấy → trả về default 5000 cho motorcycle/hourly."""
        price = PricingSetting.get_price("motorcycle", "hourly")
        self.assertEqual(price, 5000)

    def test_get_price_not_found_returns_default_car_monthly(self):
        """Không tìm thấy → trả về default 800000 cho car/monthly."""
        price = PricingSetting.get_price("car", "monthly")
        self.assertEqual(price, 800000)

    def test_get_price_not_found_returns_default_bicycle_monthly(self):
        """Không tìm thấy → trả về default 50000 cho bicycle/monthly."""
        price = PricingSetting.get_price("bicycle", "monthly")
        self.assertEqual(price, 50000)

    def test_get_price_not_found_returns_default_car_hourly(self):
        """Không tìm thấy → trả về default 30000 cho car/hourly."""
        price = PricingSetting.get_price("car", "hourly")
        self.assertEqual(price, 30000)

    def test_get_price_not_found_returns_default_bicycle_hourly(self):
        """Không tìm thấy → trả về default 0 cho bicycle/hourly (miễn phí)."""
        price = PricingSetting.get_price("bicycle", "hourly")
        self.assertEqual(price, 0)

    # --- get_price: is_active = False → không tìm thấy → fallback ---------

    def test_get_price_inactive_setting_fallback(self):
        """Setting không active → fallback về giá mặc định."""
        PricingSetting.objects.create(
            vehicle_type="motorcycle",
            package_type="monthly",
            price=999999,  # Giá sai, nhưng is_active=False
            is_active=False,
        )
        price = PricingSetting.get_price("motorcycle", "monthly")
        # Fallback = 100000 (giá mặc định từ defaults dict)
        self.assertEqual(price, 100000)

    # --- Dữ liệu biên ------------------------------------------------------

    def test_get_price_zero_boundary(self):
        """Giá = 0 vẫn được lưu và trả về đúng."""
        PricingSetting.objects.create(
            vehicle_type="bicycle",
            package_type="hourly",
            price=0,
            is_active=True,
        )
        price = PricingSetting.get_price("bicycle", "hourly")
        self.assertEqual(price, 0)

    def test_get_price_unknown_combination_returns_zero(self):
        """Combination không tồn tại trong defaults → trả về 0."""
        price = PricingSetting.get_price("truck", "yearly")
        self.assertEqual(price, 0)


# ===========================================================================
# Tests cho PricingService (pricing app)
# ===========================================================================

class PricingServiceModelTests(TestCase):
    """Kiểm tra pricing/models.py::PricingService."""

    def test_create_pricing_service(self):
        """Tạo PricingService thành công."""
        ps = PricingService.objects.create(
            vehicle_type="Xe máy",
            customer_type="Khách vãng lai",
            price=5000,
            unit="VNĐ",
            duration="/lượt",
            is_active=True,
        )
        self.assertEqual(ps.price, 5000)
        self.assertEqual(ps.vehicle_type, "Xe máy")

    def test_str_representation(self):
        """__str__ chứa loại khách, loại xe và giá."""
        ps = PricingService.objects.create(
            vehicle_type="Ô tô",
            customer_type="Khách gửi tháng",
            price=800000,
            unit="VNĐ",
            duration="/tháng",
            is_active=True,
        )
        s = str(ps)
        self.assertIn("Ô tô", s)
        self.assertIn("800,000", s)

    def test_formatted_price(self):
        """formatted_price() trả về chuỗi có dấu phẩy."""
        ps = PricingService(price=Decimal("1500000"))
        self.assertEqual(ps.formatted_price(), "1,500,000")

    def test_formatted_price_zero(self):
        """formatted_price() với giá = 0."""
        ps = PricingService(price=Decimal("0"))
        self.assertEqual(ps.formatted_price(), "0")

    # --- get_price: tìm thấy -----------------------------------------------

    def test_get_price_found(self):
        """Tìm thấy active pricing → trả về giá."""
        PricingService.objects.create(
            vehicle_type="Xe máy",
            customer_type="Khách gửi tháng",
            price=120000,
            unit="VNĐ",
            duration="/tháng",
            is_active=True,
        )
        price = PricingService.get_price("Xe máy", "Khách gửi tháng")
        self.assertEqual(price, 120000)

    # --- get_price: không tìm thấy → trả về 0 ------------------------------

    def test_get_price_not_found_returns_zero(self):
        """Không tìm thấy → trả về 0."""
        price = PricingService.get_price("Xe máy", "Khách gửi tháng")
        self.assertEqual(price, 0)

    # --- get_price: inactive → không tìm thấy → 0 --------------------------

    def test_get_price_inactive_returns_zero(self):
        """Setting inactive → DoesNotExist → trả về 0."""
        PricingService.objects.create(
            vehicle_type="Xe đạp",
            customer_type="Khách vãng lai",
            price=2000,
            unit="VNĐ",
            duration="/lượt",
            is_active=False,
        )
        price = PricingService.get_price("Xe đạp", "Khách vãng lai")
        self.assertEqual(price, 0)

    def test_unique_together_vehicle_customer(self):
        """(vehicle_type, customer_type) phải duy nhất."""
        from django.db import IntegrityError
        PricingService.objects.create(
            vehicle_type="Ô tô",
            customer_type="Khách vãng lai",
            price=30000,
            unit="VNĐ",
            duration="/lượt",
            is_active=True,
        )
        with self.assertRaises(IntegrityError):
            PricingService.objects.create(
                vehicle_type="Ô tô",
                customer_type="Khách vãng lai",
                price=40000,
                unit="VNĐ",
                duration="/lượt",
                is_active=True,
            )


# ===========================================================================
# Tests cho pricing_list view  (GET /parking/pricing/)
# ===========================================================================

class PricingListViewTests(TestCase):
    """Kiểm tra parking/views.py::pricing_list."""

    def setUp(self):
        self.client = Client()
        self.nv = make_nhanvien()
        self.client.force_login(self.nv)
        self.url = reverse("parking:pricing_list")
        # Tạo một số PricingSetting
        PricingSetting.objects.create(
            vehicle_type="motorcycle", package_type="monthly",
            price=100000, is_active=True,
        )
        PricingSetting.objects.create(
            vehicle_type="car", package_type="hourly",
            price=30000, is_active=True,
        )

    def test_get_returns_200(self):
        """GET /parking/pricing/ trả về 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_context_contains_monthly_and_hourly(self):
        """Context chứa monthly_prices và hourly_prices."""
        response = self.client.get(self.url)
        self.assertIn("monthly_prices", response.context)
        self.assertIn("hourly_prices", response.context)

    def test_requires_login(self):
        """Chưa đăng nhập → redirect."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


# ===========================================================================
# Tests cho admin_pricing_settings view  (GET+POST /parking/admin/pricing/)
# ===========================================================================

class AdminPricingSettingsViewTests(TestCase):
    """Kiểm tra parking/views.py::admin_pricing_settings."""

    def setUp(self):
        self.client = Client()
        self.admin = make_admin()
        self.client.force_login(self.admin)
        self.url = reverse("parking:admin_pricing_settings")

    def test_get_returns_200(self):
        """GET /parking/admin/pricing/ trả về 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_context_contains_vehicle_types_and_package_types(self):
        """Context có vehicle_types, package_types và pricing_data."""
        response = self.client.get(self.url)
        self.assertIn("vehicle_types", response.context)
        self.assertIn("package_types", response.context)
        self.assertIn("pricing_data", response.context)

    def test_post_creates_or_updates_pricing(self):
        """POST với giá hợp lệ → tạo hoặc cập nhật PricingSetting."""
        data = {
            "price_motorcycle_hourly": "6000",
            "price_car_monthly": "900000",
            "price_bicycle_hourly": "0",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

        ps = PricingSetting.objects.filter(
            vehicle_type="motorcycle", package_type="hourly"
        ).first()
        self.assertIsNotNone(ps)
        self.assertEqual(float(ps.price), 6000.0)

    def test_post_invalid_price_value_skips(self):
        """POST với giá không phải số → bỏ qua (continue), không crash."""
        data = {"price_car_hourly": "abc"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

    def test_post_empty_price_sets_zero(self):
        """POST với value rỗng → price=0."""
        data = {"price_bicycle_monthly": ""}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        ps = PricingSetting.objects.filter(
            vehicle_type="bicycle", package_type="monthly"
        ).first()
        if ps:
            self.assertEqual(float(ps.price), 0.0)

    def test_non_admin_cannot_access(self):
        """Nhân viên không phải admin → bị từ chối (redirect)."""
        self.client.logout()
        nv = make_nhanvien("nv2_price", "nvpass2!")
        self.client.force_login(nv)
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
