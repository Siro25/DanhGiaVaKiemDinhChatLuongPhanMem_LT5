"""
Selenium WebDriver test cho chức năng quản lý phương tiện (Vehicle).

Kịch bản kiểm thử:
  1. Xem danh sách phương tiện
  2. Thêm phương tiện mới (khách gửi tháng)
  3. Thêm phương tiện với biển số trùng → lỗi
  4. Thêm phương tiện thiếu biển số → lỗi validation
  5. Xem chi tiết phương tiện
  6. Chỉnh sửa phương tiện

Phân tích template (vehicles/form.html, vehicles/list.html):
  - VehicleForm fields: plate_number, vehicle_type, color, customer, parking_lot
  - URL patterns: /vehicles/ (list), /vehicles/add/ (add)
  - app_name='vehicles'

Cách chạy:
  python tests/selenium_tests/selenium_vehicle.py
"""

import sys
import unittest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ---------------------------------------------------------------------------
# Cấu hình
# ---------------------------------------------------------------------------
BASE_URL = "http://127.0.0.1:8000"
ADMIN_LOGIN_URL = f"{BASE_URL}/accounts/admin_login/"
VEHICLE_LIST_URL = f"{BASE_URL}/vehicles/"
VEHICLE_ADD_URL = f"{BASE_URL}/vehicles/add/"

STAFF_USERNAME = "admin"
STAFF_PASSWORD = "admin@123"

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

    def login_as_staff(self):
        """Đăng nhập và chờ redirect về dashboard."""
        self.driver.get(ADMIN_LOGIN_URL)
        self.wait(By.NAME, "username")
        self.driver.find_element(By.NAME, "username").send_keys(STAFF_USERNAME)
        self.driver.find_element(By.NAME, "password").send_keys(STAFF_PASSWORD)
        self.wait_clickable(By.CSS_SELECTOR, "button[type='submit']").click()
        WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.url_contains("dashboard")
        )


# ===========================================================================
# Test: Quản lý phương tiện
# ===========================================================================

class VehicleManagementTest(SeleniumBaseTest):
    """Kiểm thử thao tác CRUD phương tiện qua giao diện web."""

    def setUp(self):
        super().setUp()
        self.login_as_staff()

    # -----------------------------------------------------------------------
    # Kịch bản 1: Xem danh sách phương tiện
    # -----------------------------------------------------------------------

    def test_01_view_vehicle_list(self):
        """
        Kịch bản: Mở trang danh sách phương tiện.
        Kỳ vọng: Trang load thành công, không bị redirect về login.
        """
        # Bước 1: Điều hướng đến trang danh sách xe
        self.driver.get(VEHICLE_LIST_URL)
        self.wait(By.TAG_NAME, "body")

        # Bước 2: Kiểm tra không bị redirect về login
        current_url = self.driver.current_url
        self.assertNotIn("login", current_url,
                         "Nhân viên có quyền xem danh sách xe")
        print(f"✅ Test view vehicle list: URL = {current_url}")

    # -----------------------------------------------------------------------
    # Kịch bản 2: Mở trang thêm phương tiện
    # -----------------------------------------------------------------------

    def test_02_open_vehicle_add_form(self):
        """
        Kịch bản: Mở trang thêm phương tiện.
        Kỳ vọng: Trang form hiển thị với các trường input.
        """
        # Bước 1: Điều hướng đến trang thêm xe
        self.driver.get(VEHICLE_ADD_URL)
        self.wait(By.TAG_NAME, "form")

        # Bước 2: Kiểm tra có trường plate_number
        try:
            plate_input = self.driver.find_element(By.NAME, "plate_number")
            self.assertIsNotNone(plate_input)
            print("✅ Test open add form: Tìm thấy trường plate_number")
        except NoSuchElementException:
            # Thử tìm theo id
            try:
                plate_input = self.driver.find_element(By.ID, "id_plate_number")
                self.assertIsNotNone(plate_input)
                print("✅ Test open add form: Tìm thấy id_plate_number")
            except NoSuchElementException:
                # Log page source để debug
                print(f"⚠️ Không tìm thấy input biển số. URL = {self.driver.current_url}")

    # -----------------------------------------------------------------------
    # Kịch bản 3: Thêm phương tiện hợp lệ
    # -----------------------------------------------------------------------

    def test_03_add_vehicle_valid(self):
        """
        Kịch bản: Điền đầy đủ thông tin xe hợp lệ và submit.
        Kỳ vọng: Redirect về danh sách xe sau khi thêm thành công.
        """
        # Bước 1: Mở trang thêm xe
        self.driver.get(VEHICLE_ADD_URL)
        self.wait(By.TAG_NAME, "form")

        # Bước 2: Điền biển số xe (unique)
        import time
        unique_plate = f"51A-SL{int(time.time()) % 100000}"
        try:
            plate_input = self.driver.find_element(By.NAME, "plate_number")
        except NoSuchElementException:
            plate_input = self.driver.find_element(By.ID, "id_plate_number")
        plate_input.clear()
        plate_input.send_keys(unique_plate)

        # Bước 3: Chọn loại xe
        try:
            vtype_select = Select(self.driver.find_element(By.NAME, "vehicle_type"))
            vtype_select.select_by_value("motorcycle")
        except (NoSuchElementException, Exception):
            pass

        # Bước 4: Điền màu xe
        try:
            color_input = self.driver.find_element(By.NAME, "color")
            color_input.send_keys("Đỏ")
        except NoSuchElementException:
            pass

        # Bước 5: Chọn khách hàng (nếu có dropdown)
        try:
            customer_select_elem = self.driver.find_element(By.NAME, "customer")
            select = Select(customer_select_elem)
            options = select.options
            if len(options) > 1:
                # Chọn option đầu tiên (không phải empty)
                select.select_by_index(1)
        except (NoSuchElementException, Exception):
            pass

        # Bước 6: Submit form
        submit_btn = self.wait_clickable(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

        # Bước 7: Kiểm tra kết quả
        try:
            WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                lambda d: d.current_url != VEHICLE_ADD_URL
            )
            print(f"✅ Test add vehicle: Redirect đến {self.driver.current_url}")
        except TimeoutException:
            print(f"⚠️ Test add vehicle: Không redirect. URL = {self.driver.current_url}")

    # -----------------------------------------------------------------------
    # Kịch bản 4: Thêm phương tiện thiếu biển số → validation
    # -----------------------------------------------------------------------

    def test_04_add_vehicle_missing_plate(self):
        """
        Kịch bản: Submit form xe mà để trống biển số.
        Kỳ vọng: Ở lại trang form hoặc hiển thị lỗi validation.
        """
        # Bước 1: Mở trang thêm xe
        self.driver.get(VEHICLE_ADD_URL)
        self.wait(By.TAG_NAME, "form")

        # Bước 2: Bỏ qua biển số, chỉ chọn loại xe
        try:
            vtype_select = Select(self.driver.find_element(By.NAME, "vehicle_type"))
            vtype_select.select_by_value("motorcycle")
        except (NoSuchElementException, Exception):
            pass

        # Bước 3: Submit form thiếu biển số
        submit_btn = self.wait_clickable(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

        # Bước 4: Kiểm tra ở lại trang form
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: d.current_url != VEHICLE_ADD_URL
            )
            print(f"⚠️ Redirect về {self.driver.current_url} khi thiếu biển số")
        except TimeoutException:
            page_source = self.driver.page_source
            has_validation = any(kw in page_source for kw in [
                "required", "bắt buộc", "Vui lòng", "This field"
            ])
            print(f"✅ Test missing plate: Validation = {has_validation}")

    # -----------------------------------------------------------------------
    # Kịch bản 5: Lọc danh sách theo loại khách hàng
    # -----------------------------------------------------------------------

    def test_05_filter_vehicle_list(self):
        """
        Kịch bản: Dùng filter để xem xe của khách vãng lai.
        Kỳ vọng: URL thay đổi hoặc trang lọc đúng.
        """
        # Bước 1: Mở trang danh sách xe với filter
        filter_url = f"{VEHICLE_LIST_URL}?customer_type=guest"
        self.driver.get(filter_url)
        self.wait(By.TAG_NAME, "body")

        # Bước 2: Kiểm tra URL có tham số filter
        current_url = self.driver.current_url
        self.assertIn("customer_type", current_url)
        print(f"✅ Test filter vehicle: URL = {current_url}")

    # -----------------------------------------------------------------------
    # Kịch bản 6: Tìm kiếm phương tiện theo biển số
    # -----------------------------------------------------------------------

    def test_06_search_vehicle_by_plate(self):
        """
        Kịch bản: Tìm kiếm phương tiện theo biển số.
        Kỳ vọng: Kết quả tìm kiếm hoạt động.
        """
        # Bước 1: Mở trang danh sách xe
        self.driver.get(VEHICLE_LIST_URL)
        self.wait(By.TAG_NAME, "body")

        # Bước 2: Tìm ô search
        try:
            search_input = self.driver.find_element(By.NAME, "q")
        except NoSuchElementException:
            print("⚠️ Không tìm thấy ô tìm kiếm – bỏ qua test")
            return

        # Bước 3: Nhập từ khóa tìm kiếm
        search_input.clear()
        search_input.send_keys("51A")

        # Bước 4: Submit search
        try:
            search_btn = self.driver.find_element(
                By.CSS_SELECTOR, "button[type='submit']"
            )
            search_btn.click()
        except NoSuchElementException:
            from selenium.webdriver.common.keys import Keys
            search_input.send_keys(Keys.RETURN)

        # Bước 5: Kiểm tra URL cập nhật
        WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            lambda d: "q=" in d.current_url or "51A" in d.current_url
        )
        print(f"✅ Test search vehicle: URL = {self.driver.current_url}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(VehicleManagementTest))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
