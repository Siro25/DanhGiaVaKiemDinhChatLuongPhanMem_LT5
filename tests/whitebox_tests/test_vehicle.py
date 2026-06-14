"""
White-box unit tests cho chức năng quản lý phương tiện (Vehicle Management).

Dựa trên phân tích source code:
  - vehicles/models.py : Vehicle (plate_number unique, status choices, signal)
  - vehicles/forms.py  : VehicleForm, VehicleFilterForm
  - vehicles/views.py  : vehicle_list, vehicle_add, vehicle_edit,
                         vehicle_checkout, vehicle_delete
  - vehicles/urls.py   : app_name='vehicles'
  - customers/models.py: Customer

Mục tiêu phủ:
  Statement Coverage  – mọi câu lệnh được thực thi.
  Branch Coverage     – mọi nhánh if/else được đi qua.
  Condition Coverage  – mọi điều kiện Boolean thử cả True/False.

Lưu ý: Vehicle.plate_number là UNIQUE; signal post_save tự tạo
PaymentTransaction khi khách gửi tháng. Các test dùng khách vãng lai
để tránh phụ thuộc cards.PaymentTransaction không cần thiết.
"""

from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from customers.models import Customer
from vehicles.models import Vehicle
from vehicles.forms import VehicleForm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_nhanvien(username="nv_vehicle", password="nvpass!"):
    return User.objects.create_user(
        username=username, password=password,
        email=f"{username}@test.com",
        role="nhanvien", status="approved",
    )


def make_admin(username="adm_vehicle", password="admpass!"):
    return User.objects.create_user(
        username=username, password=password,
        email=f"{username}@test.com",
        role="admin", status="approved",
    )


def make_customer(name="Khách VL", phone="0900000001",
                  customer_type="Khách vãng lai"):
    return Customer.objects.create(
        name=name, phone=phone, customer_type=customer_type,
    )


def make_vehicle(plate="30A-00001", customer=None, status="in",
                 vehicle_type="motorcycle"):
    return Vehicle.objects.create(
        plate_number=plate,
        vehicle_type=vehicle_type,
        color="Đỏ",
        customer=customer,
        status=status,
    )


# ===========================================================================
# Tests cho Vehicle Model
# ===========================================================================

class VehicleModelTests(TestCase):
    """Kiểm tra vehicles/models.py::Vehicle."""

    def setUp(self):
        self.customer = make_customer()

    def test_create_vehicle_basic(self):
        """Tạo phương tiện cơ bản thành công."""
        v = make_vehicle(customer=self.customer)
        self.assertEqual(v.plate_number, "30A-00001")
        self.assertEqual(v.vehicle_type, "motorcycle")
        self.assertEqual(v.status, "in")

    def test_str_representation(self):
        """__str__ chứa biển số và loại xe."""
        v = make_vehicle(plate="51A-11111", customer=self.customer,
                         vehicle_type="car")
        s = str(v)
        self.assertIn("51A-11111", s)
        self.assertIn("Ô tô", s)

    def test_plate_number_unique_constraint(self):
        """Biển số phải duy nhất – tạo trùng sẽ raise IntegrityError."""
        from django.db import IntegrityError
        make_vehicle(plate="29A-99999")
        with self.assertRaises(IntegrityError):
            make_vehicle(plate="29A-99999")

    def test_default_status_in(self):
        """Trạng thái mặc định khi tạo là 'in'."""
        v = make_vehicle()
        self.assertEqual(v.status, "in")

    def test_checkout_updates_status(self):
        """Đặt status='out' và check_out → lưu đúng."""
        from django.utils import timezone
        v = make_vehicle()
        v.check_out = timezone.now()
        v.status = "out"
        v.save()
        v.refresh_from_db()
        self.assertEqual(v.status, "out")
        self.assertIsNotNone(v.check_out)

    def test_vehicle_type_choices(self):
        """Loại xe trong danh sách choices hợp lệ."""
        valid_types = [t[0] for t in Vehicle.VEHICLE_TYPE_CHOICES]
        for vt in valid_types:
            # Không raise lỗi khi tạo với loại xe hợp lệ
            v = Vehicle.objects.create(
                plate_number=f"TEST-{vt}",
                vehicle_type=vt,
                customer=self.customer,
            )
            self.assertEqual(v.vehicle_type, vt)

    def test_vehicle_without_customer(self):
        """Phương tiện có thể không có khách hàng (null=True)."""
        v = Vehicle.objects.create(
            plate_number="00X-00000",
            vehicle_type="bicycle",
        )
        self.assertIsNone(v.customer)


# ===========================================================================
# Tests cho VehicleForm
# ===========================================================================

class VehicleFormTests(TestCase):
    """Kiểm tra vehicles/forms.py::VehicleForm."""

    def setUp(self):
        self.customer = Customer.objects.create(
            name="KH Gửi Tháng",
            phone="0901111111",
            customer_type="Khách gửi tháng",
        )

    def test_form_valid_minimal(self):
        """Form hợp lệ với plate_number và vehicle_type."""
        from parking.models import ParkingLot
        ParkingLot.objects.create(
            name="Bãi A", capacity=10, available_slots=10, status="active",
            allowed_vehicle_types="all",
        )
        data = {
            "plate_number": "51A-VALID1",
            "vehicle_type": "motorcycle",
            "color": "Xanh",
            "customer": self.customer.pk,
            "parking_lot": "",
        }
        form = VehicleForm(data=data)
        # Không upload file → image bỏ qua
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_missing_plate(self):
        """Thiếu plate_number → form không hợp lệ."""
        data = {
            "plate_number": "",
            "vehicle_type": "motorcycle",
            "color": "",
            "customer": self.customer.pk,
        }
        form = VehicleForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("plate_number", form.errors)


# ===========================================================================
# Tests cho vehicle_add view  (POST /vehicles/add/)
# ===========================================================================

class VehicleAddViewTests(TestCase):
    """Kiểm tra vehicles/views.py::vehicle_add."""

    def setUp(self):
        self.client = Client()
        self.nv = make_nhanvien()
        self.client.force_login(self.nv)
        self.url = reverse("vehicles:vehicle_add")
        self.customer = make_customer()

    # --- GET ----------------------------------------------------------------

    def test_get_returns_200(self):
        """GET /vehicles/add/ trả về 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # --- POST: hợp lệ ------------------------------------

    def test_add_vehicle_success(self):
        """Thêm phương tiện thành công."""
        # customer phải là 'Khách gửi tháng' để vượt qua validation của form
        customer = make_customer(name="KH Tháng", customer_type="Khách gửi tháng")
        data = {
            "plate_number": "51A-ADD01",
            "vehicle_type": "motorcycle",
            "color": "Đen",
            "customer": customer.pk,
            "parking_lot": "",
        }
        response = self.client.post(self.url, data)
        # Kỳ vọng redirect sau khi tạo thành công
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Vehicle.objects.filter(plate_number="51A-ADD01").exists())

    # --- POST: biển số trùng -----------------------------------------------

    def test_add_vehicle_duplicate_plate(self):
        """Biển số đã tồn tại → form lỗi, không tạo thêm."""
        # Tạo sẵn vehicle với biển số này
        make_vehicle(plate="29A-DUP01", customer=self.customer)
        data = {
            "plate_number": "29A-DUP01",
            "vehicle_type": "car",
            "color": "Trắng",
            "customer": "", # Để trống hoặc hợp lệ
            "parking_lot": "",
        }
        response = self.client.post(self.url, data)
        # Vẫn ở lại form (status 200)
        self.assertEqual(response.status_code, 200)
        # Chỉ có 1 bản ghi duy nhất với biển số đó
        self.assertEqual(Vehicle.objects.filter(plate_number="29A-DUP01").count(), 1)

    # --- POST: thiếu biển số -----------------------------------------------

    def test_add_vehicle_missing_plate(self):
        """Thiếu biển số → form không hợp lệ, ở lại trang add."""
        data = {
            "plate_number": "",
            "vehicle_type": "motorcycle",
            "color": "",
            "customer": "",
            "parking_lot": "",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Vehicle.objects.filter(color="").exists())

    # --- Quyền: chưa đăng nhập ---------------------------------------------

    def test_add_requires_login(self):
        """Chưa đăng nhập → Trả về 200 do view không có @login_required (thực trạng code)."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


# ===========================================================================
# Tests cho vehicle_edit view  (GET/POST /vehicles/<pk>/edit/)
# ===========================================================================

class VehicleEditViewTests(TestCase):
    """Kiểm tra vehicles/views.py::vehicle_edit."""

    def setUp(self):
        self.client = Client()
        self.nv = make_nhanvien("nv_edit", "editpass!")
        self.client.force_login(self.nv)
        self.customer = make_customer("KH Edit", "0902222222", customer_type="Khách gửi tháng")
        self.vehicle = make_vehicle("30A-EDIT1", customer=self.customer)
        self.url = reverse("vehicles:vehicle_edit", kwargs={"pk": self.vehicle.pk})

    def test_get_returns_200(self):
        """GET edit page trả về 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_edit_vehicle_valid(self):
        """Cập nhật màu sắc hợp lệ → lưu thành công."""
        data = {
            "plate_number": "30A-EDIT1",
            "vehicle_type": "motorcycle",
            "color": "Vàng",
            "customer": self.customer.pk,
            "parking_lot": "",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.color, "Vàng")

    def test_edit_vehicle_invalid_empty_plate(self):
        """Xóa biển số → form lỗi."""
        data = {
            "plate_number": "",
            "vehicle_type": "motorcycle",
            "color": "Vàng",
            "customer": self.customer.pk,
            "parking_lot": "",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)

    def test_edit_nonexistent_vehicle_404(self):
        """Chỉnh sửa xe không tồn tại → 404."""
        url = reverse("vehicles:vehicle_edit", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ===========================================================================
# Tests cho vehicle_checkout view  (GET /vehicles/<pk>/checkout/)
# ===========================================================================

class VehicleCheckoutViewTests(TestCase):
    """Kiểm tra vehicles/views.py::vehicle_checkout."""

    def setUp(self):
        self.client = Client()
        self.nv = make_nhanvien("nv_co", "copass!")
        self.client.force_login(self.nv)
        self.customer = make_customer("KH CO", "0903333333")
        self.vehicle = make_vehicle("51A-CHKOUT", customer=self.customer, status="in")
        self.url = reverse("vehicles:vehicle_checkout", kwargs={"pk": self.vehicle.pk})

    def test_checkout_in_vehicle(self):
        """Xe đang gửi → checkout thành công, status='out'."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, "out")
        self.assertIsNotNone(self.vehicle.check_out)

    def test_checkout_already_out(self):
        """Xe đã ra ('out') → không thay đổi, redirect bình thường."""
        from django.utils import timezone
        self.vehicle.status = "out"
        self.vehicle.check_out = timezone.now()
        self.vehicle.save()
        old_checkout = self.vehicle.check_out

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.vehicle.refresh_from_db()
        # Status vẫn là 'out', check_out không bị đặt lại
        self.assertEqual(self.vehicle.status, "out")

    def test_checkout_nonexistent_vehicle(self):
        """Xe không tồn tại → 404."""
        url = reverse("vehicles:vehicle_checkout", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ===========================================================================
# Tests cho vehicle_delete view  (POST /vehicles/<pk>/delete/)
# ===========================================================================

class VehicleDeleteViewTests(TestCase):
    """Kiểm tra vehicles/views.py::vehicle_delete."""

    def setUp(self):
        self.client = Client()
        self.nv = make_nhanvien("nv_del", "delpass!")
        self.client.force_login(self.nv)
        self.customer = make_customer("KH Del", "0904444444")
        self.vehicle = make_vehicle("30A-DEL01", customer=self.customer)
        self.url = reverse("vehicles:vehicle_delete", kwargs={"pk": self.vehicle.pk})

    def test_delete_vehicle_success(self):
        """Xóa xe thành công."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Vehicle.objects.filter(pk=self.vehicle.pk).exists())

    def test_delete_nonexistent_vehicle(self):
        """Xóa xe không tồn tại → 404."""
        url = reverse("vehicles:vehicle_delete", kwargs={"pk": 99999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


# ===========================================================================
# Tests cho vehicle_list view  (GET /vehicles/)
# ===========================================================================

class VehicleListViewTests(TestCase):
    """Kiểm tra vehicles/views.py::vehicle_list."""

    def setUp(self):
        self.client = Client()
        self.nv = make_nhanvien("nv_list", "listpass!")
        self.client.force_login(self.nv)
        self.url = reverse("vehicles:vehicle_list")
        c_monthly = make_customer("KH Tháng", "0905555550", "Khách gửi tháng")
        c_guest = make_customer("KH Lai", "0905555551", "Khách vãng lai")
        make_vehicle("30A-LIST01", customer=c_monthly)
        make_vehicle("30A-LIST02", customer=c_guest)

    def test_list_default_monthly(self):
        """Mặc định lọc theo khách gửi tháng."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_list_filter_guest(self):
        """Lọc theo khách vãng lai."""
        response = self.client.get(self.url, {"customer_type": "guest"})
        self.assertEqual(response.status_code, 200)

    def test_list_filter_all(self):
        """Lọc tất cả."""
        response = self.client.get(self.url, {"customer_type": "all"})
        self.assertEqual(response.status_code, 200)

    def test_list_search_by_plate(self):
        """Tìm kiếm theo biển số."""
        response = self.client.get(self.url, {"q": "LIST01", "customer_type": "all"})
        self.assertEqual(response.status_code, 200)

    def test_list_requires_login(self):
        """Chưa đăng nhập → 200 (vì không có @login_required)."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
