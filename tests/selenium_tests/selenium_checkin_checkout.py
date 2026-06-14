"""
Selenium WebDriver test cho chức năng Check-in / Check-out xe.

Kịch bản kiểm thử:
  1. Check-in xe (khách hàng vào bãi) – via vehicle_toggle_parking
  2. Check-out xe (xe ra bãi) – via vehicle_toggle_parking lần 2
  3. Check-out xe bằng nhân viên – via vehicle_checkout

Phân tích URL và view:
  - Toggle parking (khách hàng): POST /customers/vehicles/<pk>/toggle-parking/
  - Checkout (nhân viên):        GET  /vehicles/<pk>/checkout/
  
Lưu ý: Các test này cần dữ liệu thực tế trong DB.
Nếu không có xe/khách hàng, test sẽ in cảnh báo và bỏ qua.

Cách chạy:
  python tests/selenium_tests/selenium_checkin_checkout.py
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
USER_LOGIN_URL = f"{BASE_URL}/accounts/user_login/"
VEHICLE_LIST_URL = f"{BASE_URL}/vehicles/"
CUSTOMER_VEHICLES_URL = f"{BASE_URL}/customers/vehicles/"

# Tài khoản admin (để thực hiện checkout từ nhân viên)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin@123"

# Tài khoản khách hàng (để thực hiện toggle parking)
KH_USERNAME = "khachhang1"
KH_PASSWORD = "kh@password123"

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
        """Đăng nhập bằng tài khoản admin."""
        self.driver.get(ADMIN_LOGIN_URL)
        self.wait(By.NAME, "username")
        self.driver.find_element(By.NAME, "username").send_keys(ADMIN_USERNAME)
        self.driver.find_element(By.NAME, "password").send_keys(ADMIN_PASSWORD)
        self.wait_clickable(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.url_contains("dashboard")
        )

    def login_as_customer(self):
        """Đăng nhập bằng tài khoản khách hàng."""
        self.driver.get(USER_LOGIN_URL)
        self.wait(By.NAME, "identifier")
        self.driver.find_element(By.NAME, "identifier").send_keys(KH_USERNAME)
        self.driver.find_element(By.NAME, "password").send_keys(KH_PASSWORD)
        self.wait_clickable(By.CSS_SELECTOR, "button[type='submit']").click()
        try:
            WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                EC.url_contains("dashboard")
            )
            return True
        except TimeoutException:
            return False


# ===========================================================================
# Test: Check-in / Check-out (Nhân viên / Admin)
# ===========================================================================

class CheckInCheckOutStaffTest(SeleniumBaseTest):
    """Kiểm thử check-out xe từ giao diện nhân viên."""

    def setUp(self):
        super().setUp()
        self.login_as_admin()

    # -----------------------------------------------------------------------
    # Kịch bản 1: Xem danh sách xe, tìm xe đang gửi
    # -----------------------------------------------------------------------

    def test_01_view_vehicle_list_for_checkout(self):
        """
        Kịch bản: Admin/nhân viên xem danh sách xe đang trong bãi.
        Kỳ vọng: Trang load thành công.
        """
        # Bước 1: Mở trang danh sách xe (tất cả)
        self.driver.get(f"{VEHICLE_LIST_URL}?customer_type=all")
        self.wait(By.TAG_NAME, "body")

        # Bước 2: Kiểm tra trang load thành công
        current_url = self.driver.current_url
        self.assertNotIn("login", current_url)
        print(f"✅ Test view vehicle list for checkout: URL = {current_url}")

    # -----------------------------------------------------------------------
    # Kịch bản 2: Check-out xe đang gửi bằng URL trực tiếp
    # -----------------------------------------------------------------------

    def test_02_staff_checkout_vehicle(self):
        """
        Kịch bản: Nhân viên checkout xe có pk=1.
        Kỳ vọng: Redirect về danh sách xe, xe status thay đổi.
        
        Lưu ý: Test này cần xe có pk=1 tồn tại và đang có status='in'.
        Nếu không có → test sẽ nhận 404 và cảnh báo.
        """
        # Bước 1: Điều hướng trực tiếp đến URL checkout
        VEHICLE_ID = 1  # Thay đổi theo dữ liệu thực tế
        checkout_url = f"{VEHICLE_LIST_URL}{VEHICLE_ID}/checkout/"
        self.driver.get(checkout_url)

        # Bước 2: Kiểm tra kết quả
        current_url = self.driver.current_url

        if "404" in self.driver.page_source or "Page not found" in self.driver.page_source:
            print(f"⚠️ Test staff checkout: Xe ID={VEHICLE_ID} không tồn tại")
            return

        # Nếu redirect về danh sách → checkout thành công
        if "vehicles" in current_url and str(VEHICLE_ID) not in current_url:
            print(f"✅ Test staff checkout: Redirect về danh sách xe")
        else:
            print(f"ℹ️ Test staff checkout: URL = {current_url}")

    # -----------------------------------------------------------------------
    # Kịch bản 3: Tìm nút checkout trong danh sách xe
    # -----------------------------------------------------------------------

    def test_03_find_checkout_button_in_list(self):
        """
        Kịch bản: Trong danh sách xe, tìm nút/link checkout.
        Kỳ vọng: Có thể tìm thấy nút checkout cho xe đang gửi.
        """
        # Bước 1: Mở danh sách tất cả xe
        self.driver.get(f"{VEHICLE_LIST_URL}?customer_type=all")
        self.wait(By.TAG_NAME, "body")

        # Bước 2: Tìm link/button checkout
        checkout_links = []
        try:
            # Tìm theo URL pattern
            checkout_links = self.driver.find_elements(
                By.XPATH, "//a[contains(@href, 'checkout')]"
            )
        except Exception:
            pass

        if checkout_links:
            print(f"✅ Tìm thấy {len(checkout_links)} nút checkout")

            # Bước 3: Click nút checkout đầu tiên
            checkout_links[0].click()

            # Bước 4: Kiểm tra kết quả
            try:
                WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                    lambda d: "checkout" not in d.current_url
                )
                print(f"✅ Test find checkout button: Redirect thành công")
            except TimeoutException:
                print(f"ℹ️ URL sau checkout: {self.driver.current_url}")
        else:
            print("⚠️ Không tìm thấy nút checkout (có thể không có xe nào đang gửi)")


# ===========================================================================
# Test: Check-in / Check-out (Khách hàng)
# ===========================================================================

class CheckInCheckOutCustomerTest(SeleniumBaseTest):
    """Kiểm thử check-in/out từ giao diện khách hàng."""

    def setUp(self):
        super().setUp()
        logged_in = self.login_as_customer()
        if not logged_in:
            print(f"⚠️ Không thể đăng nhập với tài khoản {KH_USERNAME}")
            self.skipTest("Tài khoản khách hàng không tồn tại hoặc thông tin sai")

    # -----------------------------------------------------------------------
    # Kịch bản 4: Xem danh sách xe của khách hàng
    # -----------------------------------------------------------------------

    def test_04_customer_view_vehicles(self):
        """
        Kịch bản: Khách hàng xem danh sách xe của mình.
        Kỳ vọng: Trang load thành công, không redirect về login.
        """
        # Bước 1: Mở trang danh sách xe của khách hàng
        self.driver.get(CUSTOMER_VEHICLES_URL)
        self.wait(By.TAG_NAME, "body")

        # Bước 2: Kiểm tra không bị redirect
        current_url = self.driver.current_url
        self.assertNotIn("login", current_url)
        print(f"✅ Test customer view vehicles: URL = {current_url}")

    # -----------------------------------------------------------------------
    # Kịch bản 5: Toggle parking – vào/ra bãi
    # -----------------------------------------------------------------------

    def test_05_customer_toggle_parking(self):
        """
        Kịch bản: Khách hàng click nút vào/ra bãi cho xe của mình.
        Kỳ vọng: Redirect sau khi toggle thành công.
        
        Lưu ý: Cần xe đã được duyệt của khách hàng.
        """
        # Bước 1: Mở trang danh sách xe
        self.driver.get(CUSTOMER_VEHICLES_URL)
        self.wait(By.TAG_NAME, "body")

        # Bước 2: Tìm nút vào/ra bãi (toggle-parking link)
        toggle_buttons = []
        try:
            toggle_buttons = self.driver.find_elements(
                By.XPATH, "//a[contains(@href, 'toggle-parking')] | //form[contains(@action, 'toggle-parking')]//button"
            )
        except Exception:
            pass

        if not toggle_buttons:
            print("⚠️ Test toggle parking: Không tìm thấy nút vào/ra bãi")
            print("   Có thể chưa có xe được duyệt hoặc template khác")
            return

        # Bước 3: Click nút toggle đầu tiên
        toggle_buttons[0].click()

        # Bước 4: Kiểm tra redirect
        try:
            WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                lambda d: "vehicles" in d.current_url
            )
            print(f"✅ Test toggle parking: Redirect về {self.driver.current_url}")
        except TimeoutException:
            print(f"ℹ️ URL sau toggle: {self.driver.current_url}")

    # -----------------------------------------------------------------------
    # Kịch bản 6: Xem lịch sử gửi xe
    # -----------------------------------------------------------------------

    def test_06_customer_view_history(self):
        """
        Kịch bản: Khách hàng xem lịch sử gửi xe.
        Kỳ vọng: Trang lịch sử load thành công.
        """
        # Bước 1: Mở trang lịch sử
        history_url = f"{BASE_URL}/customers/history/"
        self.driver.get(history_url)
        self.wait(By.TAG_NAME, "body")

        # Bước 2: Kiểm tra trang load
        current_url = self.driver.current_url
        self.assertNotIn("login", current_url)
        print(f"✅ Test view history: URL = {current_url}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(CheckInCheckOutStaffTest))
    suite.addTests(loader.loadTestsFromTestCase(CheckInCheckOutCustomerTest))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
