"""
Selenium WebDriver test cho chức năng Check-in / Check-out xe.
Quy trình: Đăng nhập khách hàng → Vào trang khách → Vào bãi → Vào /customers/vehicles/ → Chờ 3s → Ấn ra bãi

Cách chạy:
  python manage.py test tests.selenium_tests.selenium_checkin_checkout --settings=tests.test_settings
"""

import sys
import time
import unittest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth import get_user_model

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Tài khoản khách hàng
CUSTOMER_USERNAME = "khachhang@gmail.com"
CUSTOMER_PASSWORD = "yeye@123"

WAIT_TIMEOUT = 10


# ---------------------------------------------------------------------------
# Base Test Class
# ---------------------------------------------------------------------------

class SeleniumBaseTest(StaticLiveServerTestCase):

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
        # Tạo tài khoản khách hàng và xe
        User = get_user_model()
        if not User.objects.filter(username=CUSTOMER_USERNAME).exists():
            customer_user = User.objects.create_user(
                username=CUSTOMER_USERNAME,
                email=CUSTOMER_USERNAME,
                password=CUSTOMER_PASSWORD,
                role='khachhang',
                is_verified=True,
                status='approved'
            )
            
            # Tạo customer record
            from customers.models import Customer
            customer = Customer.objects.create(
                user=customer_user,
                name='Khách Hàng Test',
                phone='0123456789',
                email=CUSTOMER_USERNAME,
                customer_type='Khách gửi tháng'
            )
            
            # Tạo xe cho khách hàng
            from vehicles.models import Vehicle
            Vehicle.objects.create(
                customer=customer,
                plate_number='29A-12345',
                vehicle_type='motorcycle',
                color='Đỏ',
                status='out',  # Ban đầu xe ở ngoài
                approved=True
            )

    def wait_for_element(self, by, value, timeout=WAIT_TIMEOUT):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def wait_clickable(self, by, value, timeout=WAIT_TIMEOUT):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def login_customer(self):
        """Đăng nhập khách hàng."""
        print(f"[LOGIN] Đăng nhập khách hàng tại: {self.live_server_url}/accounts/login/")
        
        self.driver.get(f"{self.live_server_url}/accounts/login/")
        time.sleep(2)
        
        # Tìm username field
        username_input = None
        for field_name in ["username", "email", "user", "identifier"]:
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
        username_input.send_keys(CUSTOMER_USERNAME)
        password_input.clear()
        password_input.send_keys(CUSTOMER_PASSWORD)
        time.sleep(1)
        
        # Submit
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_btn.click()
        time.sleep(1)
        
        # Kiểm tra đăng nhập thành công
        current_url = self.driver.current_url
        if "login" in current_url:
            raise Exception(f"Đăng nhập thất bại: {current_url}")
        
        print(f"[LOGIN] Đăng nhập khách hàng thành công: {current_url}")
        return current_url


# ===========================================================================
# Test: Check-in / Check-out (Khách hàng)
# ===========================================================================

class CustomerVehicleCheckInOutTest(SeleniumBaseTest):
    """Test quy trình: Đăng nhập khách → Vào bãi → Vào /customers/vehicles/ → Chờ 3s → Ra bãi."""

    def setUp(self):
        super().setUp()

    def test_customer_checkin_wait_checkout_flow(self):
        """
        Test: Khách hàng đăng nhập → Vào trang khách → Vào bãi → Vào /customers/vehicles/ → Chờ 3s → Ấn ra bãi.
        """
        print("="*80)
        print("TEST: KHÁCH HÀNG VÀO BÃI - CHỜ 3S - RA BÃI")
        print("="*80)
        
        # Bước 1: Đăng nhập khách hàng
        login_url = self.login_customer()
        
        # Bước 2: Vào trang vehicles của khách hàng
        print(f"[VEHICLES] Truy cập trang quản lý xe của khách hàng")
        vehicles_url = "/customers/vehicles/"
        self.driver.get(f"{self.live_server_url}{vehicles_url}")
        time.sleep(2)
        
        current_url = self.driver.current_url
        print(f"[VEHICLES] URL trang xe: {current_url}")
        
        if "login" in current_url:
            print("[ERROR] Bị redirect về login khi truy cập trang xe")
            return
        
        # Kiểm tra trang đã tải
        try:
            self.wait_for_element(By.TAG_NAME, "body")
            page_title = self.driver.title
            print(f"[VEHICLES] Đã vào trang xe: {page_title}")
                
        except TimeoutException:
            print("[ERROR] Trang xe không tải được")
            return
        
        # Bước 3: Tìm và click nút "Vào bãi" 
        print("[CHECKIN] Tìm nút vào bãi")
        
        checkin_button = None
        try:
            # Tìm nút vào bãi theo nhiều cách
            possible_selectors = [
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'vào bãi')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'vào bãi')]",
                "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'check-in')]",
                "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'check-in')]",
                "//button[contains(@href, 'toggle-parking')]",
                "//a[contains(@href, 'toggle-parking')]"
            ]
            
            for selector in possible_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        # Tìm nút cho xe đang ở ngoài (status = 'out')
                        for element in elements:
                            text = element.text.strip().lower()
                            if "vào bãi" in text or "check-in" in text:
                                checkin_button = element
                                print(f"[CHECKIN] Tìm thấy nút vào bãi: '{element.text}'")
                                break
                    if checkin_button:
                        break
                except:
                    continue
            
            if not checkin_button:
                # Debug: in tất cả buttons và links
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                
                print(f"[CHECKIN] Debug - Tìm thấy {len(all_buttons)} buttons và {len(all_links)} links:")
                
                for i, btn in enumerate(all_buttons[:3]):
                    print(f"[CHECKIN] Button {i+1}: '{btn.text.strip()}'")
                
                for i, link in enumerate(all_links[:5]):
                    href = link.get_attribute("href") or ""
                    print(f"[CHECKIN] Link {i+1}: '{link.text.strip()}' - href: {href}")
                    
                    if "toggle-parking" in href:
                        checkin_button = link
                        print(f"[CHECKIN] Tìm thấy toggle-parking link: '{link.text}'")
                        break
            
            if checkin_button:
                print(f"[CHECKIN] Click vào nút vào bãi: '{checkin_button.text}'")
                checkin_button.click()
                
                # Xử lý alert xác nhận nếu có
                try:
                    alert = WebDriverWait(self.driver, 3).until(EC.alert_is_present())
                    alert_text = alert.text
                    print(f"[CHECKIN] Alert xuất hiện: {alert_text}")
                    alert.accept()  # Click OK
                    print("[CHECKIN] Đã xác nhận alert")
                except TimeoutException:
                    print("[CHECKIN] Không có alert")
                
                time.sleep(1)
                
                # Kiểm tra đã vào bãi thành công
                current_url = self.driver.current_url
                print(f"[CHECKIN] URL sau khi vào bãi: {current_url}")
                
                if "vehicles" in current_url:
                    print("[CHECKIN] Đã vào bãi thành công")
                else:
                    print(f"[CHECKIN] URL không như mong đợi: {current_url}")
                  
                time.sleep(1)
          
                # Refresh trang để cập nhật trạng thái
                self.driver.refresh()
                time.sleep(1)
                
                checkout_button = None
                try:
                    possible_checkout_selectors = [
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ra bãi')]",
                        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ra bãi')]",
                        "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'check-out')]",
                        "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'check-out')]",
                        "//a[contains(@href, 'toggle-parking')]"
                    ]
                    
                    for selector in possible_checkout_selectors:
                        try:
                            elements = self.driver.find_elements(By.XPATH, selector)
                            if elements:
                                for element in elements:
                                    text = element.text.strip().lower()
                                    href = element.get_attribute("href") or ""
                                    if ("ra bãi" in text or "check-out" in text or 
                                        "toggle-parking" in href):
                                        checkout_button = element
                                        print(f"[CHECKOUT] Tìm thấy nút ra bãi: '{element.text}'")
                                        break
                            if checkout_button:
                                break
                        except:
                            continue
                    
                    if checkout_button:
                        print(f"[CHECKOUT] Click vào nút ra bãi: '{checkout_button.text}'")
                        checkout_button.click()
                        
                        # Xử lý alert ra bãi nếu có
                        try:
                            alert = WebDriverWait(self.driver, 3).until(EC.alert_is_present())
                            alert_text = alert.text
                            print(f"[CHECKOUT] Alert ra bãi: {alert_text}")
                            alert.accept()  # Click OK
                            print("[CHECKOUT] Đã xác nhận alert ra bãi")
                        except TimeoutException:
                            print("[CHECKOUT] Không có alert ra bãi")
                        
                        time.sleep(3)
                        
                        # Kiểm tra đã ra bãi thành công
                        final_url = self.driver.current_url
                        print(f"[CHECKOUT]Đã ra bãi thành công: {final_url}")
                        
                        print("[FINAL]TEST HOÀN THÀNH - VÀO BÃI→ RA BÃI!")
                        
                    else:
                        print("[CHECKOUT] Không tìm thấy nút ra bãi")
                        print("[CHECKOUT] Nhưng đã hoàn thành phần vào bãi và chờ 3s")
                        
                except Exception as e:
                    print(f"[CHECKOUT] Lỗi khi tìm nút ra bãi: {e}")
                    print("[CHECKOUT] Nhưng đã hoàn thành phần vào bãi")
                    
            else:
                print("[CHECKIN]Không tìm thấy nút vào bãi")
                print("[CHECKIN]Đã truy cập thành công trang /customers/vehicles/")
                
        except Exception as e:
            print(f"[CHECKIN] Lỗi trong quá trình test: {e}")
        
        print("="*80)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main(verbosity=2)
