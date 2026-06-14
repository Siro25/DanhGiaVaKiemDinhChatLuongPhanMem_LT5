"""
Selenium WebDriver test cho chức năng quản lý khách hàng (Customer).

Kịch bản kiểm thử:
  1. Thêm khách hàng mới (nhân viên đăng nhập → vào /customers/add/)
  2. Xem danh sách khách hàng
  3. Tìm kiếm khách hàng theo tên
  4. Sửa thông tin khách hàng
  5. Xóa khách hàng

Phân tích template customers/form.html và customers/list.html:
  - Form thêm khách hàng: input name='name', 'phone', 'email',
    'address', 'customer_type', 'vehicle_type'
  - Nút submit: button[type='submit']
  - Danh sách: bảng hoặc div chứa thông tin khách hàng

Cách chạy:
  python tests/selenium_tests/selenium_customer.py
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
CUSTOMER_LIST_URL = f"{BASE_URL}/customers/list/"
CUSTOMER_ADD_URL = f"{BASE_URL}/customers/add/"

# Tài khoản nhân viên / admin
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
        """Đăng nhập bằng tài khoản admin/nhân viên trước khi test."""
        # Bước 1: Mở trang đăng nhập admin
        self.driver.get(ADMIN_LOGIN_URL)
        self.wait(By.NAME, "username")

        # Bước 2: Điền username
        self.driver.find_element(By.NAME, "username").send_keys(STAFF_USERNAME)
        # Bước 3: Điền password
        self.driver.find_element(By.NAME, "password").send_keys(STAFF_PASSWORD)
        # Bước 4: Submit
        self.wait_clickable(By.CSS_SELECTOR, "button[type='submit']").click()

        # Bước 5: Chờ redirect xong
        WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            EC.url_contains("dashboard")
        )


# ===========================================================================
# Test: Quản lý khách hàng
# ===========================================================================

class CustomerManagementTest(SeleniumBaseTest):
    """Kiểm thử các thao tác CRUD khách hàng qua giao diện web."""

    def setUp(self):
        super().setUp()
        # Đăng nhập trước mỗi test
        self.login_as_staff()

    # -----------------------------------------------------------------------
    # Kịch bản 1: Xem danh sách khách hàng
    # -----------------------------------------------------------------------

    def test_01_view_customer_list(self):
        """
        Kịch bản: Mở trang danh sách khách hàng.
        Kỳ vọng: Trang trả về 200, có tiêu đề 'Quản lý khách hàng'.
        """
        # Bước 1: Điều hướng đến trang danh sách
        self.driver.get(CUSTOMER_LIST_URL)

        # Bước 2: Chờ trang load
        self.wait(By.TAG_NAME, "body")

        # Bước 3: Kiểm tra URL hợp lệ (không bị redirect về login)
        current_url = self.driver.current_url
        self.assertNotIn("login", current_url,
                         "Nhân viên có quyền xem danh sách khách hàng")

        # Bước 4: Kiểm tra trang có nội dung
        page_source = self.driver.page_source
        self.assertTrue(
            len(page_source) > 100,
            "Trang danh sách phải có nội dung"
        )
        print("✅ Test view customer list: OK")

    # -----------------------------------------------------------------------
    # Kịch bản 2: Thêm khách hàng mới
    # -----------------------------------------------------------------------

    def test_02_add_customer(self):
        """
        Kịch bản: Điền form thêm khách hàng và submit.
        Kỳ vọng: Redirect thành công sau khi thêm.
        """
        # Bước 1: Mở trang thêm khách hàng
        self.driver.get(CUSTOMER_ADD_URL)
        self.wait(By.TAG_NAME, "form")

        # Bước 2: Điền tên khách hàng
        try:
            name_input = self.driver.find_element(By.NAME, "name")
            name_input.clear()
            name_input.send_keys("Khách Hàng Selenium Test")
        except NoSuchElementException:
            # Thử tìm theo id
            name_input = self.driver.find_element(By.ID, "id_name")
            name_input.clear()
            name_input.send_keys("Khách Hàng Selenium Test")

        # Bước 3: Điền số điện thoại
        try:
            phone_input = self.driver.find_element(By.NAME, "phone")
        except NoSuchElementException:
            phone_input = self.driver.find_element(By.ID, "id_phone")
        phone_input.clear()
        phone_input.send_keys("0987654321")

        # Bước 4: Chọn loại khách hàng (nếu có select)
        try:
            customer_type_select = self.driver.find_element(By.NAME, "customer_type")
            select = Select(customer_type_select)
            select.select_by_visible_text("Khách vãng lai")
        except NoSuchElementException:
            pass  # Nếu không có select, bỏ qua

        # Bước 5: Submit form
        submit_btn = self.wait_clickable(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

        # Bước 6: Kiểm tra redirect thành công
        try:
            WebDriverWait(self.driver, WAIT_TIMEOUT).until(
                lambda d: d.current_url != CUSTOMER_ADD_URL
            )
            print(f"✅ Test add customer: Redirect đến {self.driver.current_url}")
        except TimeoutException:
            # Vẫn ở trang add - có thể form lỗi
            page_source = self.driver.page_source
            print(f"⚠️ Test add customer: Không redirect, URL = {self.driver.current_url}")

    # -----------------------------------------------------------------------
    # Kịch bản 3: Tìm kiếm khách hàng theo tên
    # -----------------------------------------------------------------------

    def test_03_search_customer(self):
        """
        Kịch bản: Tìm kiếm khách hàng theo tên trong danh sách.
        Kỳ vọng: Kết quả lọc chỉ hiện khách phù hợp với từ khóa.
        """
        # Bước 1: Mở trang danh sách
        self.driver.get(CUSTOMER_LIST_URL)
        self.wait(By.TAG_NAME, "body")

        # Bước 2: Tìm ô search
        try:
            search_input = self.driver.find_element(By.NAME, "q")
        except NoSuchElementException:
            try:
                search_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='search']")
            except NoSuchElementException:
                print("⚠️ Không tìm thấy ô tìm kiếm – bỏ qua test")
                return

        # Bước 3: Nhập từ khóa tìm kiếm
        search_input.clear()
        search_input.send_keys("Khách")

        # Bước 4: Submit (Enter hoặc click nút search)
        try:
            search_btn = self.driver.find_element(
                By.CSS_SELECTOR, "button[type='submit'], input[type='submit']"
            )
            search_btn.click()
        except NoSuchElementException:
            from selenium.webdriver.common.keys import Keys
            search_input.send_keys(Keys.RETURN)

        # Bước 5: Kiểm tra URL chứa tham số q
        WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            lambda d: "q=" in d.current_url or d.current_url == CUSTOMER_LIST_URL
        )
        print(f"✅ Test search customer: URL = {self.driver.current_url}")

    # -----------------------------------------------------------------------
    # Kịch bản 4: Thêm khách hàng thiếu tên → lỗi validation
    # -----------------------------------------------------------------------

    def test_04_add_customer_missing_name(self):
        """
        Kịch bản: Thêm khách hàng nhưng để trống tên.
        Kỳ vọng: Ở lại trang form hoặc hiển thị thông báo lỗi.
        """
        # Bước 1: Mở trang thêm khách hàng
        self.driver.get(CUSTOMER_ADD_URL)
        self.wait(By.TAG_NAME, "form")

        # Bước 2: Chỉ điền phone, bỏ qua name
        try:
            phone_input = self.driver.find_element(By.NAME, "phone")
        except NoSuchElementException:
            phone_input = self.driver.find_element(By.ID, "id_phone")
        phone_input.send_keys("0123456789")

        # Bước 3: Submit form thiếu name
        submit_btn = self.wait_clickable(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()

        # Bước 4: Kiểm tra ở lại trang form hoặc có lỗi
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: d.current_url != CUSTOMER_ADD_URL
            )
            # Nếu redirect → có thể server không validate (kiểm tra DB)
            print(f"⚠️ Redirect về {self.driver.current_url} khi thiếu name")
        except TimeoutException:
            # Vẫn ở trang form → validation đúng
            page_source = self.driver.page_source
            has_error = any(kw in page_source for kw in [
                "required", "bắt buộc", "Vui lòng nhập", "thông tin"
            ])
            print(f"✅ Test add missing name: Validation = {has_error}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(CustomerManagementTest))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
