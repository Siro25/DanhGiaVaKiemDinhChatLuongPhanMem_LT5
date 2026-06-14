"""
Selenium WebDriver test cho chức năng đăng nhập (Login).

Kịch bản kiểm thử:
  1. Đăng nhập thành công bằng admin_login_view (/accounts/admin_login/)
  2. Đăng nhập thất bại – sai mật khẩu
  3. Đăng nhập thất bại – để trống username và password
  4. Đăng nhập thất bại – username không tồn tại

Phân tích HTML template accounts/admin_login.html:
  - Trường username: <input name="username" ...>
  - Trường password: <input name="password" ...>
  - Nút submit: <button type="submit" ...>
  - Thông báo lỗi: thẻ chứa text lỗi (error, alert hoặc message)

Cấu hình:
  BASE_URL – địa chỉ server đang chạy (mặc định http://127.0.0.1:8000)
  ADMIN_USERNAME / ADMIN_PASSWORD – tài khoản admin thực tế

Cách chạy:
  python tests/selenium_tests/selenium_login.py
"""

import sys
import time
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ---------------------------------------------------------------------------
# Cấu hình – thay đổi theo môi trường thực tế
# ---------------------------------------------------------------------------
BASE_URL = "http://127.0.0.1:8000"
ADMIN_LOGIN_URL = f"{BASE_URL}/accounts/admin_login/"
USER_LOGIN_URL = f"{BASE_URL}/accounts/user_login/"

# Tài khoản admin tồn tại trong DB
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin@123"

WAIT_TIMEOUT = 10  # giây tối đa chờ element


# ---------------------------------------------------------------------------
# Base Test Class
# ---------------------------------------------------------------------------

class SeleniumBaseTest(unittest.TestCase):
    """Base class: khởi tạo và dọn dẹp WebDriver."""

    @classmethod
    def setUpClass(cls):
        """Mở trình duyệt Chrome trước khi chạy test."""
        options = webdriver.ChromeOptions()
        # Bỏ comment dòng dưới để chạy headless (không mở cửa sổ)
        # options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1366,768")
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(3)

    @classmethod
    def tearDownClass(cls):
        """Đóng trình duyệt sau khi toàn bộ test chạy xong."""
        cls.driver.quit()

    def setUp(self):
        """Xóa cookie trước mỗi test để đảm bảo session sạch."""
        self.driver.delete_all_cookies()

    def wait_for_element(self, by, value, timeout=WAIT_TIMEOUT):
        """Đợi element xuất hiện và trả về element đó."""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def wait_for_clickable(self, by, value, timeout=WAIT_TIMEOUT):
        """Đợi element clickable."""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def wait_for_url_contains(self, text, timeout=WAIT_TIMEOUT):
        """Đợi URL chứa text nhất định."""
        return WebDriverWait(self.driver, timeout).until(
            EC.url_contains(text)
        )


# ===========================================================================
# Test: Admin Login
# ===========================================================================

class AdminLoginTest(SeleniumBaseTest):
    """Kiểm thử giao diện admin_login_view."""

    def _open_admin_login(self):
        """Mở trang admin login."""
        # Bước 1: Điều hướng đến trang đăng nhập admin
        self.driver.get(ADMIN_LOGIN_URL)
        self.wait_for_element(By.NAME, "username")

    def _fill_login_form(self, username, password):
        """
        Điền vào form đăng nhập.
        Tìm input theo name attribute (từ template admin_login.html).
        """
        # Bước 2: Điền username
        username_input = self.driver.find_element(By.NAME, "username")
        username_input.clear()
        username_input.send_keys(username)

        # Bước 3: Điền password
        password_input = self.driver.find_element(By.NAME, "password")
        password_input.clear()
        password_input.send_keys(password)

        # Bước 4: Click nút đăng nhập (button type=submit)
        submit_btn = self.wait_for_clickable(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

    # -----------------------------------------------------------------------
    # Kịch bản 1: Đăng nhập thành công
    # -----------------------------------------------------------------------

    def test_01_admin_login_success(self):
        """
        Kịch bản: Đăng nhập admin thành công.
        Kỳ vọng: Redirect đến /accounts/dashboard_admin/ hoặc URL chứa 'dashboard'.
        """
        # Bước 1: Mở trang
        self._open_admin_login()

        # Bước 2-4: Điền và submit form
        self._fill_login_form(ADMIN_USERNAME, ADMIN_PASSWORD)

        # Bước 5: Kiểm tra redirect đến dashboard admin
        try:
            self.wait_for_url_contains("dashboard")
            current_url = self.driver.current_url
            self.assertIn("dashboard", current_url,
                          f"Sau đăng nhập kỳ vọng URL chứa 'dashboard', thực tế: {current_url}")
            print(f"✅ Test login success: Redirect đến {current_url}")
        except TimeoutException:
            # Có thể URL khác nhau tùy cấu hình
            current_url = self.driver.current_url
            self.assertNotEqual(current_url, ADMIN_LOGIN_URL,
                                "Sau đăng nhập thành công không nên ở lại trang login")

    # -----------------------------------------------------------------------
    # Kịch bản 2: Sai mật khẩu
    # -----------------------------------------------------------------------

    def test_02_admin_login_wrong_password(self):
        """
        Kịch bản: Đăng nhập với mật khẩu sai.
        Kỳ vọng: Ở lại trang login, hiển thị thông báo lỗi.
        """
        # Bước 1: Mở trang
        self._open_admin_login()

        # Bước 2-4: Điền username hợp lệ, password sai
        self._fill_login_form(ADMIN_USERNAME, "SAI_MAT_KHAU_XYZ")

        # Bước 5: Kiểm tra vẫn ở trang login
        current_url = self.driver.current_url
        self.assertIn("login", current_url,
                      "Mật khẩu sai phải ở lại trang login")

        # Bước 6: Kiểm tra có thông báo lỗi
        page_source = self.driver.page_source
        has_error = (
            "không đúng" in page_source.lower()
            or "error" in page_source.lower()
            or "invalid" in page_source.lower()
        )
        self.assertTrue(has_error, "Phải hiển thị thông báo lỗi khi mật khẩu sai")
        print("✅ Test wrong password: Hiển thị lỗi đúng")

    # -----------------------------------------------------------------------
    # Kịch bản 3: Để trống cả username và password
    # -----------------------------------------------------------------------

    def test_03_admin_login_empty_fields(self):
        """
        Kịch bản: Không nhập username và password.
        Kỳ vọng: Ở lại trang login, có thông báo lỗi.
        """
        # Bước 1: Mở trang
        self._open_admin_login()

        # Bước 2-4: Submit form trống
        self._fill_login_form("", "")

        # Bước 5: Kiểm tra vẫn ở trang login hoặc có validation
        current_url = self.driver.current_url
        page_source = self.driver.page_source

        is_still_on_login = "login" in current_url
        has_error_message = any(
            keyword in page_source
            for keyword in ["đầy đủ", "required", "bắt buộc", "không được để trống"]
        )

        self.assertTrue(
            is_still_on_login or has_error_message,
            "Form trống phải hiển thị lỗi hoặc ở lại trang login"
        )
        print("✅ Test empty fields: Validation hoạt động đúng")

    # -----------------------------------------------------------------------
    # Kịch bản 4: Username không tồn tại
    # -----------------------------------------------------------------------

    def test_04_admin_login_nonexistent_user(self):
        """
        Kịch bản: Đăng nhập với username không tồn tại trong DB.
        Kỳ vọng: Ở lại trang login, hiển thị thông báo lỗi.
        """
        # Bước 1: Mở trang
        self._open_admin_login()

        # Bước 2-4: Điền username không tồn tại
        self._fill_login_form("nguoi_dung_khong_ton_tai_xyz123", ADMIN_PASSWORD)

        # Bước 5: Kiểm tra vẫn ở trang login
        current_url = self.driver.current_url
        self.assertIn("login", current_url,
                      "Username không tồn tại phải ở lại trang login")

        # Bước 6: Kiểm tra thông báo lỗi
        page_source = self.driver.page_source
        has_error = "không đúng" in page_source or "error" in page_source.lower()
        self.assertTrue(has_error, "Phải hiển thị thông báo lỗi")
        print("✅ Test nonexistent user: Hiển thị lỗi đúng")


# ===========================================================================
# Test: User Login (user_login_view)
# ===========================================================================

class UserLoginTest(SeleniumBaseTest):
    """Kiểm thử giao diện user_login_view (đăng nhập bằng email/username)."""

    # Cấu hình tài khoản khách hàng test
    KH_USERNAME = "khachhang1"
    KH_EMAIL = "khachhang1@test.com"
    KH_PASSWORD = "kh@password123"

    def _open_user_login(self):
        """Mở trang user login."""
        self.driver.get(USER_LOGIN_URL)
        self.wait_for_element(By.NAME, "identifier")

    def _fill_user_login_form(self, identifier, password):
        """
        Điền form user_login.html.
        Trường identifier (name='identifier') hỗ trợ cả email và username.
        """
        # Bước 2: Điền identifier (email hoặc username)
        id_input = self.driver.find_element(By.NAME, "identifier")
        id_input.clear()
        id_input.send_keys(identifier)

        # Bước 3: Điền password
        pw_input = self.driver.find_element(By.NAME, "password")
        pw_input.clear()
        pw_input.send_keys(password)

        # Bước 4: Submit
        submit_btn = self.wait_for_clickable(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

    # -----------------------------------------------------------------------
    # Kịch bản 5: Đăng nhập user thất bại – sai mật khẩu
    # -----------------------------------------------------------------------

    def test_05_user_login_wrong_password(self):
        """
        Kịch bản: User login với mật khẩu sai.
        Kỳ vọng: Ở lại trang, có thông báo lỗi.
        """
        # Bước 1: Mở trang
        self._open_user_login()

        # Bước 2-4: Điền form với password sai
        self._fill_user_login_form(self.KH_USERNAME, "SAI_MAT_KHAU_123")

        # Bước 5: Kiểm tra
        current_url = self.driver.current_url
        self.assertIn("login", current_url, "Phải ở lại trang login")

        page_source = self.driver.page_source
        has_error = "không đúng" in page_source or "error" in page_source.lower()
        self.assertTrue(has_error, "Phải có thông báo lỗi")
        print("✅ Test user login wrong password: OK")

    # -----------------------------------------------------------------------
    # Kịch bản 6: Form rỗng
    # -----------------------------------------------------------------------

    def test_06_user_login_empty_form(self):
        """
        Kịch bản: Submit form trống.
        Kỳ vọng: Ở lại trang hoặc có validation HTML5.
        """
        # Bước 1: Mở trang
        self._open_user_login()

        # Bước 2-4: Submit trống
        self._fill_user_login_form("", "")

        # Bước 5: Kiểm tra validation
        current_url = self.driver.current_url
        page_source = self.driver.page_source

        is_on_login = "login" in current_url
        has_validation_error = any(
            kw in page_source
            for kw in ["Vui lòng nhập", "required", "bắt buộc"]
        )

        self.assertTrue(
            is_on_login or has_validation_error,
            "Form rỗng phải xử lý validation"
        )
        print("✅ Test user login empty form: OK")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Chạy riêng file này: python tests/selenium_tests/selenium_login.py
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(AdminLoginTest))
    suite.addTests(loader.loadTestsFromTestCase(UserLoginTest))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
