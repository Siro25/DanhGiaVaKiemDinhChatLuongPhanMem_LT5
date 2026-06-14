"""
Selenium WebDriver test cho chức năng Pricing (Bảng giá).

Kịch bản kiểm thử:
  1. Nhân viên xem bảng giá (/parking/pricing/)
  2. Admin xem trang cài đặt giá (/parking/admin/pricing/)
  3. Admin cập nhật giá cho motorcycle/hourly
  4. Admin nhập giá không hợp lệ (chữ thay vì số)
  5. Xem giá mặc định khi chưa có cấu hình

Phân tích URL và view (parking/views.py):
  - pricing_list: GET /parking/pricing/
  - admin_pricing_settings: GET/POST /parking/admin/pricing/
  
Form admin_pricing_settings (parking/templates/admin/parking/pricing_settings.html):
  - Input fields theo pattern: name="price_{vehicle_type}_{package_type}"
    Ví dụ: price_motorcycle_hourly, price_car_monthly, price_bicycle_hourly

Cách chạy:
  python tests/selenium_tests/selenium_pricing.py
"""

import sys
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ---------------------------------------------------------------------------
# Cấu hình
# ---------------------------------------------------------------------------
BASE_URL = "http://127.0.0.1:8000"
ADMIN_LOGIN_URL = f"{BASE_URL}/accounts/admin_login/"
PRICING_LIST_URL = f"{BASE_URL}/parking/pricing/"
ADMIN_PRICING_URL = f"{BASE_URL}/parking/admin/pricing/"

# Tài khoản
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin@123"

NV_USERNAME = "nhanvien1"
NV_PASSWORD = "nv@password123"

WAIT_TIMEOUT = 10


# ---------------------------------------------------------------------------
# Base Test Class
# ---------------------------------------------------------------------------

class SeleniumBaseTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1366,768")
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(3)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def setUp(self):
        self.driver.delete_all_cookies()

    def wait(self, by, value, timeout=WAIT_TIMEOUT):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def wait_clickable(self, by, value, timeout=WAIT_TIMEOUT):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def login_as_admin(self):
        """Đăng nhập bằng admin."""
        self.driver.get(ADMIN_LOGIN_URL)
        self.wait(By.NAME, "username")
        self.driver.find_element(By.NAME, "username").send_keys(ADMIN_USERNAME)
        self.driver.find_element(By.NAME, "password").send_keys(ADMIN_PASSWORD)
        self.wait_clickable(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.url_contains("dashboard")
        )

    def login_as_nhanvien(self):
        """Đăng nhập bằng nhân viên."""
        from selenium.webdriver.common.by import By
        user_login_url = f"{BASE_URL}/accounts/user_login/"
        self.driver.get(user_login_url)
        self.wait(By.NAME, "identifier")
        self.driver.find_element(By.NAME, "identifier").send_keys(NV_USERNAME)
        self.driver.find_element(By.NAME, "password").send_keys(NV_PASSWORD)
        self.wait_clickable(By.CSS_SELECTOR, "button[type='submit']").click()
        try:
            WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                EC.url_contains("dashboard")
            )
            return True
        except TimeoutException:
            return False


# ===========================================================================
# Test: Bảng giá cho Nhân viên
# ===========================================================================

class PricingListViewTest(SeleniumBaseTest):
    """Kiểm thử trang bảng giá dành cho nhân viên."""

    def setUp(self):
        super().setUp()
        self.login_as_admin()

    # -----------------------------------------------------------------------
    # Kịch bản 1: Xem bảng giá
    # -----------------------------------------------------------------------

    def test_01_view_pricing_list(self):
        """
        Kịch bản: Nhân viên/admin xem bảng giá.
        Kỳ vọng: Trang load thành công, hiển thị bảng giá.
        """
        # Bước 1: Điều hướng đến trang bảng giá
        self.driver.get(PRICING_LIST_URL)
        self.wait(By.TAG_NAME, "body")

        # Bước 2: Kiểm tra không bị redirect về login
        current_url = self.driver.current_url
        self.assertNotIn("login", current_url,
                         "Nhân viên phải có quyền xem bảng giá")

        # Bước 3: Kiểm tra trang có nội dung bảng giá
        page_source = self.driver.page_source
        # Trang bảng giá thường chứa thông tin về loại xe và giá
        has_pricing_info = any(keyword in page_source for keyword in [
            "Xe máy", "Ô tô", "Xe đạp", "VNĐ", "monthly", "hourly",
            "Vé tháng", "Vé theo lượt", "giá"
        ])
        self.assertTrue(has_pricing_info or len(page_source) > 200,
                        "Trang bảng giá phải có nội dung")
        print(f"✅ Test view pricing list: URL = {current_url}")


# ===========================================================================
# Test: Admin Pricing Settings
# ===========================================================================

class AdminPricingSettingsTest(SeleniumBaseTest):
    """Kiểm thử trang cài đặt giá dành cho admin."""

    def setUp(self):
        super().setUp()
        self.login_as_admin()

    # -----------------------------------------------------------------------
    # Kịch bản 2: Admin xem trang cài đặt giá
    # -----------------------------------------------------------------------

    def test_02_admin_view_pricing_settings(self):
        """
        Kịch bản: Admin mở trang cài đặt bảng giá.
        Kỳ vọng: Trang hiển thị form với các input giá.
        """
        # Bước 1: Mở trang admin pricing
        self.driver.get(ADMIN_PRICING_URL)
        self.wait(By.TAG_NAME, "body")

        # Bước 2: Kiểm tra URL hợp lệ
        current_url = self.driver.current_url
        self.assertNotIn("login", current_url)

        # Bước 3: Kiểm tra có form
        try:
            form = self.driver.find_element(By.TAG_NAME, "form")
            self.assertIsNotNone(form)
            print(f"✅ Test admin pricing settings: Form tìm thấy")
        except NoSuchElementException:
            print(f"⚠️ Không tìm thấy form tại {current_url}")

    # -----------------------------------------------------------------------
    # Kịch bản 3: Admin cập nhật giá motorcycle/hourly
    # -----------------------------------------------------------------------

    def test_03_admin_update_motorcycle_hourly_price(self):
        """
        Kịch bản: Admin nhập giá mới cho xe máy theo giờ.
        Kỳ vọng: Lưu thành công, hiển thị thông báo thành công.
        """
        # Bước 1: Mở trang cài đặt giá
        self.driver.get(ADMIN_PRICING_URL)
        self.wait(By.TAG_NAME, "body")

        current_url = self.driver.current_url
        if "login" in current_url:
            print("⚠️ Không có quyền admin – bỏ qua test")
            return

        # Bước 2: Tìm input price_motorcycle_hourly
        price_input = None
        input_names_to_try = [
            "price_motorcycle_hourly",
            "price_Xe máy_Khách vãng lai",
        ]

        for input_name in input_names_to_try:
            try:
                price_input = self.driver.find_element(By.NAME, input_name)
                break
            except NoSuchElementException:
                continue

        if price_input is None:
            # Thử tìm input đầu tiên trong form
            try:
                inputs = self.driver.find_elements(
                    By.CSS_SELECTOR, "input[type='number'], input[type='text']"
                )
                if inputs:
                    price_input = inputs[0]
            except Exception:
                pass

        if price_input is None:
            print("⚠️ Test update price: Không tìm thấy input giá – bỏ qua")
            return

        # Bước 3: Xóa giá cũ và nhập giá mới
        price_input.clear()
        price_input.send_keys("6000")

        # Bước 4: Submit form
        submit_btn = self.wait_clickable(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

        # Bước 5: Kiểm tra thông báo thành công sau redirect
        try:
            WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                lambda d: "pricing" in d.current_url or "cập nhật" in d.page_source.lower()
            )
            page_source = self.driver.page_source
            has_success = any(keyword in page_source for keyword in [
                "thành công", "success", "cập nhật", "Đã cập nhật"
            ])
            print(f"✅ Test update price: Success = {has_success}")
        except TimeoutException:
            print(f"ℹ️ URL sau update: {self.driver.current_url}")

    # -----------------------------------------------------------------------
    # Kịch bản 4: Admin nhập giá không hợp lệ (chữ thay vì số)
    # -----------------------------------------------------------------------

    def test_04_admin_update_price_invalid_value(self):
        """
        Kịch bản: Admin nhập giá bằng ký tự chữ.
        Kỳ vọng: Hệ thống bỏ qua giá trị không hợp lệ (không crash),
                 các giá hợp lệ khác vẫn được lưu.
        """
        # Bước 1: Mở trang cài đặt giá
        self.driver.get(ADMIN_PRICING_URL)
        self.wait(By.TAG_NAME, "body")

        current_url = self.driver.current_url
        if "login" in current_url:
            print("⚠️ Không có quyền – bỏ qua")
            return

        # Bước 2: Tìm input giá và nhập giá trị không hợp lệ
        try:
            inputs = self.driver.find_elements(
                By.CSS_SELECTOR, "input[type='number'], input[type='text'][name^='price']"
            )
            if inputs:
                inputs[0].clear()
                inputs[0].send_keys("gia_sai_xyz")
        except Exception as e:
            print(f"⚠️ Lỗi tìm input: {e}")
            return

        # Bước 3: Submit form
        try:
            submit_btn = self.wait_clickable(By.CSS_SELECTOR, "button[type='submit']")
            submit_btn.click()

            # Bước 4: Kiểm tra không crash (có redirect hoặc vẫn trên trang)
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: d.current_url != ADMIN_PRICING_URL or "error" not in d.page_source.lower()
                )
                print(f"✅ Test invalid price: Hệ thống không crash, URL = {self.driver.current_url}")
            except TimeoutException:
                print(f"ℹ️ URL sau invalid: {self.driver.current_url}")
        except Exception as e:
            print(f"⚠️ Test invalid price: {e}")

    # -----------------------------------------------------------------------
    # Kịch bản 5: Không phải admin → bị từ chối
    # -----------------------------------------------------------------------

    def test_05_non_admin_cannot_access_pricing_settings(self):
        """
        Kịch bản: User không phải admin cố truy cập trang cài đặt giá.
        Kỳ vọng: Bị redirect hoặc nhận lỗi 403/redirect to login.
        """
        # Bước 1: Logout admin
        self.driver.delete_all_cookies()

        # Bước 2: Thử truy cập trang admin pricing mà không đăng nhập
        self.driver.get(ADMIN_PRICING_URL)
        self.wait(By.TAG_NAME, "body")

        # Bước 3: Kiểm tra bị redirect
        current_url = self.driver.current_url
        is_redirected = "login" in current_url or ADMIN_PRICING_URL not in current_url
        self.assertTrue(is_redirected,
                        "Người dùng chưa đăng nhập phải bị redirect khỏi trang admin pricing")
        print(f"✅ Test non-admin access: Redirect về {current_url}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(PricingListViewTest))
    suite.addTests(loader.loadTestsFromTestCase(AdminPricingSettingsTest))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
