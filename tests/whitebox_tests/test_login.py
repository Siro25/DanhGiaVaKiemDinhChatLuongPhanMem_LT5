"""Unit tests white-box cho chức năng đăng nhập (Login)."""

from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from accounts.forms import LoginForm


def make_user(username, password, role="admin", status="approved", email=""):
    """Tạo user test nhanh."""
    email = email or f"{username}@test.com"
    return User.objects.create_user(username=username, password=password, email=email, role=role, status=status)


class LoginFormTests(TestCase):
    """Kiểm tra LoginForm validation."""
    
    def test_01_login_form_validation(self):
        """Kiểm tra validation form: hợp lệ, identifier rỗng, password rỗng."""
        # Form hợp lệ
        form = LoginForm(data={"identifier": "testuser", "password": "secret123"})
        self.assertTrue(form.is_valid())
        
        # Identifier rỗng
        form = LoginForm(data={"identifier": "", "password": "secret123"})
        self.assertFalse(form.is_valid())
        self.assertIn("identifier", form.errors)
        
        # Password rỗng
        form = LoginForm(data={"identifier": "testuser", "password": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("password", form.errors)
        
        # Cả hai đều rỗng
        form = LoginForm(data={"identifier": "", "password": ""})
        self.assertFalse(form.is_valid())


class LoginViewTests(TestCase):
    """Kiểm tra main login view với email authentication."""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse("login")
        self.admin = make_user("admin_user", "pass@1234", role="admin")
        self.nv_approved = make_user("nv_ok", "pass@1234", role="nhanvien", status="approved")
        self.nv_pending = make_user("nv_pending", "pass@1234", role="nhanvien", status="pending")
        self.nv_rejected = make_user("nv_rejected", "pass@1234", role="nhanvien", status="rejected")
        self.khachhang = make_user("kh_user", "pass@1234", role="khachhang")
    
    def test_02_login_success_and_role_redirects(self):
        """Kiểm tra đăng nhập thành công cho các roles khác nhau."""
        # Admin login → admin_dashboard
        response = self.client.post(self.url, {"email": self.admin.email, "password": "pass@1234"})
        self.assertRedirects(response, reverse("admin_dashboard"), fetch_redirect_response=False)
        self.client.logout()
        
        # Nhân viên approved → dashboard-nhanvien
        response = self.client.post(self.url, {"email": self.nv_approved.email, "password": "pass@1234"})
        self.assertRedirects(response, reverse("dashboard-nhanvien"), fetch_redirect_response=False)
        self.client.logout()
        
        # Khách hàng → dashboard-khachhang
        response = self.client.post(self.url, {"email": self.khachhang.email, "password": "pass@1234"})
        self.assertRedirects(response, reverse("dashboard-khachhang"), fetch_redirect_response=False)
    
    def test_03_login_authentication_errors(self):
        """Kiểm tra các lỗi xác thực khác nhau."""
        # Sai mật khẩu
        response = self.client.post(self.url, {"email": self.admin.email, "password": "WRONG"})
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("không đúng" in str(m) for m in messages))
        
        # Email không tồn tại
        response = self.client.post(self.url, {"email": "nobody@test.com", "password": "pass@1234"})
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("không đúng" in str(m) for m in messages))
        
        # Email rỗng
        response = self.client.post(self.url, {"email": "", "password": "pass@1234"})
        self.assertEqual(response.status_code, 200)
    
    def test_04_employee_status_restrictions(self):
        """Kiểm tra hạn chế trạng thái nhân viên."""
        # Nhân viên pending bị chặn
        response = self.client.post(self.url, {"email": self.nv_pending.email, "password": "pass@1234"})
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("chờ" in str(m).lower() for m in messages))
        
        # Nhân viên rejected bị chặn
        response = self.client.post(self.url, {"email": self.nv_rejected.email, "password": "pass@1234"})
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("từ chối" in str(m).lower() for m in messages))


class AdminLoginViewTests(TestCase):
    """Kiểm tra admin login chuyên dụng với username authentication."""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse("admin_login")
        self.admin = make_user("superadmin", "adminpass!", role="admin")
        self.nhanvien = make_user("worker1", "workerpass!", role="nhanvien")
    
    def test_05_admin_login_success_and_validation(self):
        """Kiểm tra admin login thành công và validation errors."""
        # Admin login thành công
        response = self.client.post(self.url, {"username": "superadmin", "password": "adminpass!"})
        self.assertRedirects(response, reverse("admin_dashboard"), fetch_redirect_response=False)
        
        # Username rỗng
        response = self.client.post(self.url, {"username": "", "password": "adminpass!"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "đầy đủ")
        
        # Password rỗng
        response = self.client.post(self.url, {"username": "superadmin", "password": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "đầy đủ")
        
        # Sai mật khẩu
        response = self.client.post(self.url, {"username": "superadmin", "password": "WRONG"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "không đúng")
        
        # Role không phải admin bị từ chối
        response = self.client.post(self.url, {"username": "worker1", "password": "workerpass!"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "không có quyền")
        
        # User không tồn tại
        response = self.client.post(self.url, {"username": "ghost", "password": "pass"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "không đúng")


class UserLoginViewTests(TestCase):
    """Kiểm tra user login với hỗ trợ username/email."""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse("user_login")
        self.user = make_user("khuser1", "kh@pass123", role="khachhang", email="khuser1@example.com")
        self.nv_pending = make_user("nv_p2", "nv@pass", role="nhanvien", status="pending")
    
    def test_06_user_login_multiple_identifiers(self):
        """Kiểm tra login bằng username, email và validation."""
        # Login bằng username
        response = self.client.post(self.url, {"identifier": "khuser1", "password": "kh@pass123"})
        self.assertRedirects(response, reverse("dashboard-khachhang"), fetch_redirect_response=False)
        self.client.logout()
        
        # Login bằng email
        response = self.client.post(self.url, {"identifier": "khuser1@example.com", "password": "kh@pass123"})
        self.assertRedirects(response, reverse("dashboard-khachhang"), fetch_redirect_response=False)
        self.client.logout()
        
        # Sai mật khẩu
        response = self.client.post(self.url, {"identifier": "khuser1", "password": "WRONGPASS"})
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("không đúng" in str(m) for m in messages))
        
        # Nhân viên pending bị chặn
        response = self.client.post(self.url, {"identifier": "nv_p2", "password": "nv@pass"})
        self.assertEqual(response.status_code, 200)
        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("chờ" in str(m).lower() for m in messages))
        
        # Form rỗng
        response = self.client.post(self.url, {"identifier": "", "password": ""})
        self.assertEqual(response.status_code, 200)
    
    def test_07_login_redirect_handling(self):
        """Kiểm tra safe redirect với next parameter."""
        safe_next = reverse("dashboard-khachhang")
        data = {"identifier": "khuser1", "password": "kh@pass123", "next": safe_next}
        response = self.client.post(self.url, data)
        self.assertRedirects(response, safe_next, fetch_redirect_response=False)
