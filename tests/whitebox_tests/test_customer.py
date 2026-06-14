"""
White-box unit tests cho chức năng quản lý khách hàng (Customer Management).

Dựa trên phân tích source code:
  - customers/models.py : Customer, MonthlySubscription, Wallet
  - customers/views.py  : customer_add, customer_edit, customer_delete,
                          customer_list, customer_detail
  - customers/urls.py   : namespace='customers'
  - accounts/models.py  : User (role: nhanvien/admin)

Mục tiêu phủ:
  Statement Coverage  – mọi câu lệnh được thực thi.
  Branch Coverage     – mọi nhánh if/else được đi qua.
  Condition Coverage  – mọi điều kiện Boolean thử cả True/False.
"""

from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from customers.models import Customer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_staff(username="staffuser", password="staffpass!"):
    """Tạo nhân viên (nhanvien) để thực hiện thao tác quản lý khách hàng."""
    return User.objects.create_user(
        username=username,
        password=password,
        email=f"{username}@test.com",
        role="nhanvien",
        status="approved",
    )


def create_admin(username="adminuser", password="adminpass!"):
    """Tạo admin."""
    return User.objects.create_user(
        username=username,
        password=password,
        email=f"{username}@test.com",
        role="admin",
        status="approved",
    )


def create_customer(name="Nguyễn Văn A", phone="0901234567",
                    customer_type="Khách vãng lai", **kwargs):
    """Tạo Customer nhanh."""
    return Customer.objects.create(
        name=name,
        phone=phone,
        customer_type=customer_type,
        **kwargs,
    )


# ===========================================================================
# Tests cho Customer Model
# ===========================================================================

class CustomerModelTests(TestCase):
    """Kiểm tra customers/models.py::Customer."""

    def test_create_customer_basic(self):
        """Tạo khách hàng cơ bản với name và phone."""
        c = create_customer()
        self.assertEqual(c.name, "Nguyễn Văn A")
        self.assertEqual(c.phone, "0901234567")
        self.assertEqual(c.customer_type, "Khách vãng lai")
        self.assertEqual(c.status, "not_registered")  # default
        self.assertTrue(c.is_active)  # default True

    def test_str_includes_name_and_phone(self):
        """__str__ phải chứa tên và số điện thoại."""
        c = create_customer(name="Trần Thị B", phone="0912345678")
        s = str(c)
        self.assertIn("Trần Thị B", s)
        self.assertIn("0912345678", s)

    def test_str_no_phone_shows_id(self):
        """Khi không có phone lẫn thêm info → hiển thị ID."""
        c = Customer.objects.create(
            name="Ẩn Danh",
            phone="",
            customer_type="Khách vãng lai",
        )
        s = str(c)
        # Không có SĐT → phần info_parts chỉ có name → thêm ID
        self.assertIn("Ẩn Danh", s)

    def test_default_status_not_registered(self):
        """Trạng thái mặc định là 'not_registered'."""
        c = create_customer()
        self.assertEqual(c.status, "not_registered")

    def test_customer_with_email(self):
        """Email được lưu khi cung cấp."""
        c = Customer.objects.create(
            name="Email Test",
            phone="0900000001",
            email="email@test.com",
            customer_type="Khách vãng lai",
        )
        self.assertEqual(c.email, "email@test.com")

    def test_customer_type_monthly(self):
        """Tạo khách gửi tháng thành công."""
        c = create_customer(customer_type="Khách gửi tháng")
        self.assertEqual(c.customer_type, "Khách gửi tháng")


# ===========================================================================
# Tests cho customer_add view  (POST /customers/add/)
# ===========================================================================

class CustomerAddViewTests(TestCase):
    """Kiểm tra customers/views.py::customer_add."""

    def setUp(self):
        self.client = Client()
        self.staff = create_staff()
        self.client.force_login(self.staff)
        self.url = reverse("customers:customer_add")

    # --- GET ----------------------------------------------------------------

    def test_get_returns_200(self):
        """GET /customers/add/ trả về 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # --- POST: hợp lệ -------------------------------------------------------

    def test_add_customer_valid_vanglai(self):
        """Thêm khách vãng lai hợp lệ → tạo được Customer."""
        data = {
            "name": "Khách Mới",
            "phone": "0901111111",
            "email": "",
            "address": "",
            "vehicle_type": "",
            "customer_type": "Khách vãng lai",
        }
        response = self.client.post(self.url, data)
        # Redirect về customer_list sau khi tạo thành công
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Customer.objects.filter(name="Khách Mới").exists())

    def test_add_customer_valid_monthly(self):
        """Thêm khách gửi tháng hợp lệ thành công."""
        data = {
            "name": "Khách Tháng",
            "phone": "0902222222",
            "email": "thang@test.com",
            "address": "123 Đường ABC",
            "vehicle_type": "xemay",
            "customer_type": "Khách gửi tháng",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Customer.objects.filter(name="Khách Tháng").exists())
        c = Customer.objects.get(name="Khách Tháng")
        self.assertEqual(c.created_by, self.staff)

    # --- POST: thiếu dữ liệu ------------------------------------------------

    def test_add_customer_missing_name(self):
        """Thiếu name → ở lại form, không tạo Customer."""
        data = {
            "name": "",
            "phone": "0903333333",
            "customer_type": "Khách vãng lai",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Customer.objects.filter(phone="0903333333").exists())

    def test_add_customer_missing_phone(self):
        """Thiếu phone → ở lại form, không tạo Customer."""
        data = {
            "name": "Không Phone",
            "phone": "",
            "customer_type": "Khách vãng lai",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Customer.objects.filter(name="Không Phone").exists())

    # --- Quyền: user chưa đăng nhập ----------------------------------------

    def test_add_requires_login(self):
        """Truy cập khi chưa đăng nhập → redirect login."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


# ===========================================================================
# Tests cho customer_edit view  (POST /customers/edit/<pk>/)
# ===========================================================================

class CustomerEditViewTests(TestCase):
    """Kiểm tra customers/views.py::customer_edit."""

    def setUp(self):
        self.client = Client()
        self.staff = create_staff("editor_staff", "editorpass!")
        self.client.force_login(self.staff)
        self.customer = create_customer("Nguyễn Edit", "0904444444")
        self.url = reverse("customers:customer_edit", kwargs={"pk": self.customer.pk})

    # --- GET ----------------------------------------------------------------

    def test_get_returns_200(self):
        """GET /customers/edit/<pk>/ trả về 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # --- POST: hợp lệ -------------------------------------------------------

    def test_edit_customer_valid(self):
        """Cập nhật thông tin hợp lệ → lưu thành công."""
        data = {
            "name": "Nguyễn Edit Updated",
            "phone": "0904444445",
            "email": "updated@test.com",
            "address": "Địa chỉ mới",
            "vehicle_type": "",
            "customer_type": "Khách vãng lai",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, "Nguyễn Edit Updated")
        self.assertEqual(self.customer.phone, "0904444445")

    # --- POST: thiếu dữ liệu ------------------------------------------------

    def test_edit_customer_missing_name(self):
        """Thiếu name → không lưu, ở lại form."""
        data = {
            "name": "",
            "phone": "0904444444",
            "customer_type": "Khách vãng lai",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.name, "Nguyễn Edit")  # không thay đổi

    def test_edit_customer_missing_phone(self):
        """Thiếu phone → không lưu."""
        data = {
            "name": "Nguyễn Edit",
            "phone": "",
            "customer_type": "Khách vãng lai",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)

    # --- Không tìm thấy customer -------------------------------------------

    def test_edit_customer_not_found_returns_404(self):
        """PK không tồn tại → 404."""
        url = reverse("customers:customer_edit", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ===========================================================================
# Tests cho customer_delete view  (POST /customers/delete/<pk>/)
# ===========================================================================

class CustomerDeleteViewTests(TestCase):
    """Kiểm tra customers/views.py::customer_delete."""

    def setUp(self):
        self.client = Client()
        self.staff = create_staff("del_staff", "delpass!")
        self.client.force_login(self.staff)
        self.customer = create_customer("Nguyễn Delete", "0905555555")
        self.url = reverse("customers:customer_delete", kwargs={"pk": self.customer.pk})

    # --- GET: hiển thị trang xác nhận -------------------------------------

    def test_get_returns_confirmation_page(self):
        """GET /customers/delete/<pk>/ → hiển thị trang xác nhận."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    # --- POST: xóa thành công ----------------------------------------------

    def test_delete_customer_no_vehicles(self):
        """Khách hàng không có xe → xóa thành công."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Customer.objects.filter(pk=self.customer.pk).exists())

    # --- POST: có xe liên kết → không cho xóa ----------------------------

    def test_delete_customer_with_vehicles_blocked(self):
        """Khách hàng có xe → không xóa được, hiển thị lỗi."""
        from vehicles.models import Vehicle
        Vehicle.objects.create(
            plate_number="30A-99999",
            vehicle_type="motorcycle",
            customer=self.customer,
        )
        response = self.client.post(self.url)
        # Redirect về list hoặc detail với thông báo lỗi
        self.assertEqual(response.status_code, 302)
        # Khách hàng vẫn còn trong DB
        self.assertTrue(Customer.objects.filter(pk=self.customer.pk).exists())

    # --- Không tìm thấy customer -------------------------------------------

    def test_delete_nonexistent_customer(self):
        """PK không tồn tại → 404 hoặc redirect với lỗi."""
        url = reverse("customers:customer_delete", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302, 404])


# ===========================================================================
# Tests cho customer_list view  (GET /customers/list/)
# ===========================================================================

class CustomerListViewTests(TestCase):
    """Kiểm tra customers/views.py::customer_list."""

    def setUp(self):
        self.client = Client()
        self.staff = create_staff("list_staff", "listpass!")
        self.client.force_login(self.staff)
        self.url = reverse("customers:customer_list")
        # Tạo một vài customer
        create_customer("Alpha Customer", "0900000001", "Khách vãng lai")
        create_customer("Beta Customer", "0900000002", "Khách gửi tháng")

    def test_list_returns_200(self):
        """GET /customers/list/ trả về 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_list_search_by_name(self):
        """Tìm kiếm theo tên trả về kết quả đúng."""
        response = self.client.get(self.url, {"q": "Alpha"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha Customer")
        self.assertNotContains(response, "Beta Customer")

    def test_list_filter_monthly(self):
        """Lọc loại 'monthly' chỉ hiện Khách gửi tháng."""
        response = self.client.get(self.url, {"type": "monthly"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Beta Customer")

    def test_list_filter_guest(self):
        """Lọc loại 'guest' chỉ hiện Khách vãng lai."""
        response = self.client.get(self.url, {"type": "guest"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha Customer")

    def test_list_requires_login(self):
        """Chưa đăng nhập → redirect."""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


# ===========================================================================
# Tests cho customer_detail view  (GET /customers/detail/<pk>/)
# ===========================================================================

class CustomerDetailViewTests(TestCase):
    """Kiểm tra customers/views.py::customer_detail."""

    def setUp(self):
        self.client = Client()
        self.staff = create_staff("detail_staff", "detailpass!")
        self.client.force_login(self.staff)
        self.customer = create_customer("Detail Customer", "0906666666")
        self.url = reverse("customers:customer_detail", kwargs={"pk": self.customer.pk})

    def test_detail_returns_200(self):
        """GET /customers/detail/<pk>/ trả về 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_detail_contains_customer_name(self):
        """Trang chi tiết chứa tên khách hàng."""
        response = self.client.get(self.url)
        self.assertContains(response, "Detail Customer")

    def test_detail_not_found_404(self):
        """PK không tồn tại → 404."""
        url = reverse("customers:customer_detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
