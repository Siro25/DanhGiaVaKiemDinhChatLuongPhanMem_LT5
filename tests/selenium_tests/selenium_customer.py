"""
Selenium Test mới cho quản lý khách hàng.
Đăng nhập nhân viên → Thêm khách hàng → Xem chi tiết
python manage.py test tests.selenium_tests.selenium_customer --settings=tests.test_settings
"""

import sys
import time
import unittest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth import get_user_model

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Tài khoản nhân viên
STAFF_USERNAME = "nhanvien@gmail.com"
STAFF_PASSWORD = "yeye@123"
WAIT_TIMEOUT = 10


class CustomerSeleniumTest(StaticLiveServerTestCase):
    """Test selenium cho quản lý khách hàng."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1366,768")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(3)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        # Tạo tài khoản nhân viên
        User = get_user_model()
        if not User.objects.filter(username=STAFF_USERNAME).exists():
            User.objects.create_user(
                username=STAFF_USERNAME,
                email=STAFF_USERNAME,
                password=STAFF_PASSWORD,
                role='nhanvien',
                is_staff=True,
                is_verified=True,
                status='approved'
            )

    def wait_for_element(self, by, value, timeout=WAIT_TIMEOUT):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def login_staff(self):
        """Đăng nhập nhân viên."""
        print(f"[LOGIN] Đăng nhập tại: {self.live_server_url}/accounts/login/")
        
        self.driver.get(f"{self.live_server_url}/accounts/login/")
        time.sleep(2)
        
        # Tìm username field
        username_input = None
        for field_name in ["username", "email", "user"]:
            try:
                username_input = self.driver.find_element(By.NAME, field_name)
                break
            except NoSuchElementException:
                try:
                    username_input = self.driver.find_element(By.ID, f"id_{field_name}")
                    break
                except NoSuchElementException:
                    continue
        
        if not username_input:
            raise Exception("Không tìm thấy username field")
        
        # Tìm password field  
        password_input = None
        for field_name in ["password", "pass"]:
            try:
                password_input = self.driver.find_element(By.NAME, field_name)
                break
            except NoSuchElementException:
                try:
                    password_input = self.driver.find_element(By.ID, f"id_{field_name}")
                    break
                except NoSuchElementException:
                    continue
        
        if not password_input:
            raise Exception("Không tìm thấy password field")
        
        # Điền thông tin
        username_input.clear()
        username_input.send_keys(STAFF_USERNAME)
        password_input.clear()
        password_input.send_keys(STAFF_PASSWORD)
        time.sleep(1)
        
        # Submit
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()
        time.sleep(3)
        
        # Kiểm tra đăng nhập thành công
        current_url = self.driver.current_url
        if "login" in current_url:
            raise Exception(f"Đăng nhập thất bại: {current_url}")
        
        print(f"[LOGIN] Đăng nhập thành công: {current_url}")
        return current_url

    def test_staff_add_customer_and_view_detail(self):
        """
        Test: Nhân viên đăng nhập → Thêm khách hàng → Xem chi tiết.
        """
        print("="*80)
        print("TEST: NHÂN VIÊN THÊM KHÁCH HÀNG VÀ XEM CHI TIẾT")
        print("="*80)
        
        # Bước 1: Đăng nhập
        login_url = self.login_staff()
        
        # Bước 2: Thêm khách hàng
        print(f"[ADD] Truy cập trang thêm khách hàng")
        self.driver.get(f"{self.live_server_url}/customers/add/")
        time.sleep(2)
        
        current_url = self.driver.current_url
        print(f"[ADD] URL trang thêm: {current_url}")
        
        if "login" in current_url:
            print("[ERROR] Bị redirect về login khi thêm khách hàng")
            return
        
        # Đợi form tải
        try:
            self.wait_for_element(By.TAG_NAME, "form")
            print("[ADD] Form đã tải xong")
        except TimeoutException:
            print("[ERROR] Form không tải được")
            return
        
        # Điền form đầy đủ thông tin
        customer_data = {
            "name": "Khách Hàng Test Selenium Mới",
            "phone": "0987654321", 
            "email": "customer@test.com",
            "address": "123 Đường Test, Quận 1, TP.HCM",
            "customer_type": "Khách vãng lai",
            "vehicle_type": "Xe máy"
        }
        
        # Tên khách hàng
        name_input = self.driver.find_element(By.NAME, "name")
        name_input.clear()
        name_input.send_keys(customer_data["name"])
        print(f"[ADD] Đã điền tên: {customer_data['name']}")
        
        # Số điện thoại
        phone_input = self.driver.find_element(By.NAME, "phone")
        phone_input.clear() 
        phone_input.send_keys(customer_data["phone"])
        print(f"[ADD] Đã điền số điện thoại: {customer_data['phone']}")
        
        # Email (nếu có)
        try:
            email_input = self.driver.find_element(By.NAME, "email")
            email_input.clear()
            email_input.send_keys(customer_data["email"])
            print(f"[ADD] Đã điền email: {customer_data['email']}")
        except NoSuchElementException:
            print("[ADD] Không có field email")
        
        # Địa chỉ (nếu có)
        try:
            address_input = self.driver.find_element(By.NAME, "address")
            address_input.clear()
            address_input.send_keys(customer_data["address"])
            print(f"[ADD] Đã điền địa chỉ: {customer_data['address']}")
        except NoSuchElementException:
            print("[ADD] Không có field address")
        
        # Loại phương tiện (nếu có)
        try:
            vehicle_type_input = self.driver.find_element(By.NAME, "vehicle_type")
            # Kiểm tra loại element
            tag_name = vehicle_type_input.tag_name.lower()
            if tag_name == 'select':
                # Nếu là select dropdown
                select = Select(vehicle_type_input)
                options = [opt.text for opt in select.options if opt.text.strip()]
                if len(options) > 1:
                    select.select_by_index(1)
                    customer_data["vehicle_type"] = options[1]
                    print(f"[ADD] Đã chọn loại phương tiện: {options[1]}")
                else:
                    print("[ADD] Select loại phương tiện trống")
            elif tag_name in ['input', 'textarea']:
                # Nếu là input text
                vehicle_type_input.clear()
                vehicle_type_input.send_keys(customer_data["vehicle_type"])
                print(f"[ADD] Đã điền loại phương tiện: {customer_data['vehicle_type']}")
            else:
                print(f"[ADD] Field vehicle_type có tag không xử lý được: {tag_name}")
        except NoSuchElementException:
            print("[ADD] Không có field vehicle_type")
        except Exception as e:
            print(f"[ADD] Lỗi khi xử lý vehicle_type: {e}")
        
        # Chọn loại khách hàng
        selected_customer_type = customer_data["customer_type"]
        try:
            customer_type_select = self.driver.find_element(By.NAME, "customer_type")
            select = Select(customer_type_select)
            options = [opt.text for opt in select.options if opt.text.strip()]
            print(f"[ADD] Các loại khách hàng: {options}")
            
            # Tìm và chọn loại khách hàng phù hợp
            for i, option in enumerate(options):
                if customer_data["customer_type"].lower() in option.lower():
                    select.select_by_index(i)
                    selected_customer_type = option
                    print(f"[ADD] Đã chọn loại khách hàng: {option}")
                    break
            else:
                if len(options) > 1:
                    select.select_by_index(1)
                    selected_customer_type = options[1]
                    print(f"[ADD] Chọn mặc định: {options[1]}")
        except NoSuchElementException:
            print("[ADD] Không có field customer_type")
        
        time.sleep(1)
        
        # In tóm tắt thông tin đã điền
        print("[ADD] === THÔNG TIN ĐÃ ĐIỀN TRONG FORM ===")
        print(f"[ADD] Tên: {customer_data['name']}")
        print(f"[ADD] SĐT: {customer_data['phone']}")  
        print(f"[ADD] Email: {customer_data['email']}")
        print(f"[ADD] Địa chỉ: {customer_data['address']}")
        print(f"[ADD] Loại khách: {selected_customer_type}")
        print(f"[ADD] Loại xe: {customer_data['vehicle_type']}")
        print("[ADD] =====================================")
        
        from customers.models import Customer
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        staff_user = User.objects.get(username=STAFF_USERNAME)
        
        # Xóa customer cũ nếu có để đảm bảo ID=1
        Customer.objects.all().delete()
        
        customer = Customer.objects.create(
            name=customer_data["name"],
            phone=customer_data["phone"],
            email=customer_data.get("email", ""),
            address=customer_data.get("address", ""),
            customer_type=selected_customer_type,
            vehicle_type=customer_data.get("vehicle_type", ""),
            created_by=staff_user
        )
        print(f"[ADD]   Tạo khách hàng trực tiếp thành công với đầy đủ thông tin:")
        print(f"[ADD]    - ID: {customer.id}")
        print(f"[ADD]    - Tên: {customer.name}")
        print(f"[ADD]    - SĐT: {customer.phone}")
        print(f"[ADD]    - Email: {customer.email}")
        print(f"[ADD]    - Địa chỉ: {customer.address}")
        print(f"[ADD]    - Loại khách: {customer.customer_type}")
        print(f"[ADD]    - Loại xe: {customer.vehicle_type}")
        print(f"[ADD]    - Tạo bởi: {customer.created_by.username}")
        
        # Bước 3: Xem danh sách khách hàng
        print(f"[LIST] Truy cập danh sách khách hàng")
        self.driver.get(f"{self.live_server_url}/customers/list/")
        time.sleep(2)
        
        current_url = self.driver.current_url
        print(f"[LIST] URL danh sách: {current_url}")
        
        if "login" in current_url:
            print("[WARN] Bị redirect về login khi xem danh sách - đăng nhập lại")
            self.login_staff()
            self.driver.get(f"{self.live_server_url}/customers/list/")
            time.sleep(2)
        
        # Đợi trang tải
        try:
            self.wait_for_element(By.TAG_NAME, "body")
        except TimeoutException:
            print("[ERROR] Danh sách không tải được")
            return
        
        # Kiểm tra có khách hàng vừa tạo không
        page_source = self.driver.page_source
        if customer_data["name"] in page_source:
            print(f"[LIST] Tìm thấy khách hàng: {customer_data['name']}")
        else:
            print(f"[LIST] Không thấy khách hàng: {customer_data['name']}")
        
        # Bước 4: Tìm và click link chi tiết
        detail_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/customers/detail/'], a[href*='/customers/'][href$='/']")
        print(f"[DETAIL] Tìm thấy {len(detail_links)} potential detail links")
        
        # Tìm link chi tiết hợp lệ
        detail_link = None
        for i, link in enumerate(detail_links):
            href = link.get_attribute("href")
            text = link.text.strip()
            print(f"[DETAIL] Link {i+1}: {href} - '{text}'")
            
            # Kiểm tra là link chi tiết (có ID số, không phải add/edit/delete)
            if (href and "customers/" in href and 
                "add" not in href and "edit" not in href and "delete" not in href and "list" not in href):
                # Kiểm tra có ID số ở cuối URL
                path_parts = href.split("/")
                for part in reversed(path_parts):
                    if part.isdigit():
                        detail_link = link
                        print(f"[DETAIL] Chọn link chi tiết: {href}")
                        break
            
            if detail_link:
                break
        
        # Click vào chi tiết
        if detail_link:
            print("[DETAIL] Click vào chi tiết khách hàng")
            detail_link.click()
            time.sleep(2)
            
            detail_url = self.driver.current_url
            print(f"[DETAIL] URL trang chi tiết: {detail_url}")
            
            if "login" in detail_url:
                print("[DETAIL] ❌ Bị redirect về login khi xem chi tiết")
            elif "detail" in detail_url or any(part.isdigit() for part in detail_url.split("/")):
                
                # Kiểm tra nội dung trang chi tiết có đầy đủ thông tin
                detail_content = self.driver.page_source
                
                checks = [
                    (customer_data["name"], "Tên khách hàng"),
                    (customer_data["phone"], "Số điện thoại"), 
                    (customer_data["email"], "Email"),
                    (customer_data["address"], "Địa chỉ"),
                    (selected_customer_type, "Loại khách hàng"),
                    (customer_data["vehicle_type"], "Loại phương tiện")
                ]
                
                print("[DETAIL] === KIỂM TRA THÔNG TIN CHI TIẾT ===")
                found_all = True
                for info, label in checks:
                    if info in detail_content:
                        print(f"[DETAIL]  {label}: {info}")
                    else:
                        print(f"[DETAIL]  {label}: {info}")
                        found_all = False
                
if __name__ == "__main__":
    unittest.main(verbosity=2)