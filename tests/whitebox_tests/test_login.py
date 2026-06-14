"""
White-box unit tests cho chức năng đăng nhập (Login).

Dựa trên phân tích source code:
  - accounts/views.py : login_view, admin_login_view, user_login_view
  - accounts/forms.py : LoginForm
  - accounts/models.py: User (role, status)

Mục tiêu phủ:
  Statement Coverage  – mọi câu lệnh đều được thực thi ít nhất 1 lần.
  Branch Coverage     – mọi nhánh if/else được đi qua.
  Condition Coverage  – mọi điều kiện Boolean được thử cả True/False.
"""

from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from accounts.forms import LoginForm


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_user(username, password, role="admin", status="approved", email=""):
    """Tạo user test nhanh."""
    email = email or f"{username}@test.com"
    u = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        role=role,
        status=status,
    )
    return u


# ===========================================================================
# Tests cho LoginForm
# ===========================================================================

class LoginFormTests(TestCase):
    """Kiểm tra form đăng nhập LoginForm (accounts/forms.py)."""

    def test_form_valid_with_identifier_and_password(self):
        """Form hợp lệ khi cung cấp đầy đủ identifier và password."""
        data = {"identifier": "testuser", "password": "secret123"}
        form = LoginForm(data=data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_empty_identifier(self):
        """Form không hợp lệ khi identifier để trống (clean_identifier raise ValidationError)."""
        data = {"identifier": "", "password": "secret123"}
        form = LoginForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("identifier", form.errors)

    def test_form_invalid_empty_password(self):
        """Form không hợp lệ khi password để trống."""
        data = {"identifier": "testuser", "password": ""}
        form = LoginForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)

    def test_form_invalid_both_empty(self):
        """Form không hợp lệ khi cả hai trường đều trống."""
        form = LoginForm(data={"identifier": "", "password": ""})
        self.assertFalse(form.is_valid())


# ===========================================================================
# Tests cho login_view  (đăng nhập qua email – /accounts/login/)
# ===========================================================================

class LoginViewTests(TestCase):
    """
    Kiểm tra accounts/views.py::login_view.

    login_view tìm user theo email rồi authenticate bằng username.
    """

    def setUp(self):
        self.client = Client()
        self.url = reverse("login")
        self.admin_user = make_user("admin_login", "pass@1234", role="admin")
        self.nv_approved = make_user(
            "nv_ok", "pass@1234", role="nhanvien", status="approved",
            email="nv_ok@test.com"
        )
        self.nv_pending = make_user(
            "nv_pending", "pass@1234", role="nhanvien", status="pending",
            email="nv_pending@test.com"
        )
        self.nv_rejected = make_user(
            "nv_rejected", "pass@1234", role="nhanvien", status="rejected",
            email="nv_rejected@test.com"
        )
        self.kh_user = make_user(
            "kh_user", "pass@1234", role="khachhang",
            email="kh_user@test.com"
        )

    # --- GET -----------------------------------------------------------------

    def test_get_returns_200(self):
        """GET /accounts/login/ trả về 200 và hiển thị form."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    # --- POST: thành công ---------------------------------------------------

    def test_login_success_admin_redirect(self):
        """Admin đăng nhập thành công → redirect admin_dashboard."""
        response = self.client.post(
            self.url,
            {"email": self.admin_user.email, "password": "pass@1234"},
        )
        self.assertRedirects(response, reverse("admin_dashboard"), fetch_redirect_response=False)

    def test_login_success_nhanvien_redirect(self):
        """Nhân viên được duyệt đăng nhập → redirect dashboard-nhanvien."""
        response = self.client.post(
            self.url,
            {"email": self.nv_approved.email, "password": "pass@1234"},
        )
        self.assertRedirects(response, reverse("dashboard-nhanvien"), fetch_redirect_response=False)

    def test_login_success_khachhang_redirect(self):
        """Khách hàng đăng nhập → redirect dashboard-khachhang."""
        response = self.client.post(
            self.url,
            {"email": self.kh_user.email, "password": "pass@1234"},
        )
        self.assertRedirects(response, reverse("dashboard-khachhang"), fetch_redirect_response=False)

    # --- POST: sai mật khẩu ------------------------------------------------

    def test_login_wrong_password_shows_error(self):
        """Sai mật khẩu → ở lại trang login, hiện thông báo lỗi."""
        response = self.client.post(
            self.url,
            {"email": self.admin_user.email, "password": "WRONG"},
        )
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("không đúng" in str(m) for m in messages))

    # --- POST: user không tồn tại ------------------------------------------

    def test_login_nonexistent_email_shows_error(self):
        """Email không tồn tại → user là None → hiện thông báo lỗi."""
        response = self.client.post(
            self.url,
            {"email": "nobody@test.com", "password": "pass@1234"},
        )
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("không đúng" in str(m) for m in messages))

    # --- POST: dữ liệu rỗng ------------------------------------------------

    def test_login_empty_email(self):
        """Email rỗng → user_obj là None → user là None → error."""
        response = self.client.post(
            self.url, {"email": "", "password": "pass@1234"}
        )
        self.assertEqual(response.status_code, 200)

    # --- POST: nhân viên bị block ------------------------------------------

    def test_login_nhanvien_pending_blocked(self):
        """Nhân viên pending bị chặn, hiển thị cảnh báo."""
        response = self.client.post(
            self.url,
            {"email": self.nv_pending.email, "password": "pass@1234"},
        )
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("chờ" in str(m).lower() for m in messages))

    def test_login_nhanvien_rejected_blocked(self):
        """Nhân viên bị từ chối, hiển thị thông báo lỗi."""
        response = self.client.post(
            self.url,
            {"email": self.nv_rejected.email, "password": "pass@1234"},
        )
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("từ chối" in str(m).lower() for m in messages))


# ===========================================================================
# Tests cho admin_login_view  (/accounts/admin_login/)
# ===========================================================================

class AdminLoginViewTests(TestCase):
    """
    Kiểm tra accounts/views.py::admin_login_view.
    Đăng nhập bằng username (không phải email).
    """

    def setUp(self):
        self.client = Client()
        self.url = reverse("admin_login")
        self.admin_user = make_user("superadmin", "adminpass!", role="admin")
        self.nhanvien = make_user("worker1", "workerpass!", role="nhanvien")

    # --- GET -----------------------------------------------------------------

    def test_get_returns_200(self):
        """GET /accounts/admin_login/ trả về 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/admin_login.html")

    # --- POST: hợp lệ -------------------------------------------------------

    def test_admin_login_success(self):
        """Admin đăng nhập thành công → redirect admin_dashboard."""
        response = self.client.post(
            self.url,
            {"username": "superadmin", "password": "adminpass!"},
        )
        self.assertRedirects(response, reverse("admin_dashboard"), fetch_redirect_response=False)

    # --- POST: thiếu field --------------------------------------------------

    def test_admin_login_empty_username(self):
        """Username rỗng → trả về lỗi 'nhập đầy đủ'."""
        response = self.client.post(
            self.url, {"username": "", "password": "adminpass!"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "đầy đủ")

    def test_admin_login_empty_password(self):
        """Password rỗng → trả về lỗi 'nhập đầy đủ'."""
        response = self.client.post(
            self.url, {"username": "superadmin", "password": ""}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "đầy đủ")

    # --- POST: sai mật khẩu ------------------------------------------------

    def test_admin_login_wrong_password(self):
        """Sai mật khẩu → hiển thị thông báo lỗi."""
        response = self.client.post(
            self.url, {"username": "superadmin", "password": "WRONG"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "không đúng")

    # --- POST: user không phải admin ----------------------------------------

    def test_admin_login_non_admin_role(self):
        """Nhân viên cố đăng nhập vào admin_login → bị từ chối."""
        response = self.client.post(
            self.url, {"username": "worker1", "password": "workerpass!"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "không có quyền")

    # --- POST: user không tồn tại ------------------------------------------

    def test_admin_login_nonexistent_user(self):
        """Username không tồn tại → hiển thị lỗi 'không đúng'."""
        response = self.client.post(
            self.url, {"username": "ghost", "password": "pass"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "không đúng")


# ===========================================================================
# Tests cho user_login_view  (/accounts/user_login/)
# ===========================================================================

class UserLoginViewTests(TestCase):
    """
    Kiểm tra accounts/views.py::user_login_view.
    Hỗ trợ đăng nhập bằng cả email lẫn username.
    """

    def setUp(self):
        self.client = Client()
        self.url = reverse("user_login")
        self.user = make_user(
            "khuser1", "kh@pass123", role="khachhang",
            email="khuser1@example.com"
        )
        self.nv_pending = make_user(
            "nv_p2", "nv@pass", role="nhanvien", status="pending",
            email="nv_p2@example.com"
        )

    # --- GET -----------------------------------------------------------------

    def test_get_returns_200(self):
        """GET /accounts/user_login/ trả về 200."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/user_login.html")

    # --- Đăng nhập bằng username -------------------------------------------

    def test_login_by_username_success(self):
        """Đăng nhập bằng username hợp lệ thành công."""
        data = {"identifier": "khuser1", "password": "kh@pass123"}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse("dashboard-khachhang"), fetch_redirect_response=False)

    # --- Đăng nhập bằng email ----------------------------------------------

    def test_login_by_email_success(self):
        """Đăng nhập bằng email hợp lệ thành công."""
        data = {"identifier": "khuser1@example.com", "password": "kh@pass123"}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse("dashboard-khachhang"), fetch_redirect_response=False)

    # --- Sai mật khẩu -------------------------------------------------------

    def test_login_wrong_password(self):
        """Sai mật khẩu → hiển thị lỗi."""
        data = {"identifier": "khuser1", "password": "WRONGPASS"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("không đúng" in str(m) for m in messages))

    # --- Nhân viên pending --------------------------------------------------

    def test_login_nhanvien_pending_blocked(self):
        """Nhân viên có status pending bị chặn."""
        data = {"identifier": "nv_p2", "password": "nv@pass"}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("chờ" in str(m).lower() for m in messages))

    # --- Form không hợp lệ ------------------------------------------------

    def test_login_empty_form_invalid(self):
        """Form rỗng → form.is_valid() = False → không gọi authenticate."""
        data = {"identifier": "", "password": ""}
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)

    # --- Redirect an toàn (next param) -------------------------------------

    def test_login_safe_next_redirect(self):
        """Nếu `next` hợp lệ, sau login chuyển đến trang next."""
        safe_next = reverse("dashboard-khachhang")
        data = {
            "identifier": "khuser1",
            "password": "kh@pass123",
            "next": safe_next,
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, safe_next, fetch_redirect_response=False)
