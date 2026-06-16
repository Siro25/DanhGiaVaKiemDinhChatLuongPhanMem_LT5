# Hệ thống kiểm thử – Parking Management System

---

## Cấu trúc thư mục

```
tests/
├── whitebox_tests/          # Django TestCase (Unit Test)
│   ├── __init__.py
│   ├── test_login.py        # Kiểm thử đăng nhập
│   ├── test_customer.py     # Kiểm thử quản lý khách hàng
│   ├── test_vehicle.py      # Kiểm thử quản lý phương tiện
│   ├── test_parking.py      # Kiểm thử check-in/check-out
│   └── test_pricing.py      # Kiểm thử bảng giá
│
├── selenium_tests/          # Selenium WebDriver Test
│   ├── __init__.py
│   ├── selenium_login.py    # Kiểm thử đăng nhập qua trình duyệt
│   ├── selenium_customer.py # Kiểm thử quản lý khách hàng
│   ├── selenium_vehicle.py  # Kiểm thử quản lý phương tiện
│   ├── selenium_checkin_checkout.py  # Kiểm thử check-in/out
│   
└── README.md
```

---

## PHẦN 1: White-box Testing (Django TestCase)

### Phương pháp kiểm thử

| Tiêu chí | Mô tả |
|---------|-------|
| **Statement Coverage** | Mọi câu lệnh trong hàm được thực thi ≥ 1 lần |
| **Branch Coverage** | Mọi nhánh `if/else` được đi qua |
| **Condition Coverage** | Mọi biểu thức Boolean được thử cả `True` và `False` |

### Chi tiết từng file test

#### `test_login.py`
**Mô tả**: Kiểm thử 3 view đăng nhập
- `login_view` – đăng nhập bằng email
- `admin_login_view` – đăng nhập admin bằng username  
- `user_login_view` – đăng nhập bằng email hoặc username

**Các test case chính**:
- ✅ Đăng nhập thành công cho admin/nhân viên/khách hàng
- ✅ Xử lý sai mật khẩu và email không tồn tại
- ✅ Kiểm tra trạng thái nhân viên (pending/rejected)
- ✅ Validation form và safe redirect

| Test Case | Branch được cover |
|-----------|-----------------|
| Login thành công (admin/nhân viên/khách hàng) | role == 'admin/nhanvien/khachhang' |
| Sai mật khẩu | user is None |
| Email không tồn tại | user_obj is None |
| Email rỗng | email falsy |
| Nhân viên pending bị chặn | status == 'pending' |
| Nhân viên bị từ chối bị chặn | status == 'rejected' |
| Username không phải admin | role != 'admin' |
| Form rỗng | form.is_valid() = False |
| Safe next redirect | url_has_allowed_host = True/False |

#### `test_customer.py`
**Mô tả**: Kiểm thử model và CRUD khách hàng 
- Model Customer: validation, defaults, `__str__` method
- Views: thêm, sửa, xóa, danh sách khách hàng

**Các test case chính**:
- ✅ Tạo khách hàng vãng lai và gửi tháng
- ✅ Validation form và xử lý lỗi
- ✅ Tìm kiếm và lọc theo loại khách hàng
- ✅ Ràng buộc xóa khách hàng có xe liên kết

| Test Case | Branch được cover |
|-----------|-----------------|
| Tạo khách hàng cơ bản | `__str__` với phone |
| `__str__` không phone → hiển thị ID | `len(info_parts) == 1` |
| Thêm khách vãng lai hợp lệ | name and phone → True |
| Thêm khách gửi tháng hợp lệ | customer_type khác nhau |
| Thiếu name | name falsy → False |
| Thiếu phone | phone falsy → False |
| Sửa hợp lệ | name and phone → True |
| Sửa thiếu name | không lưu |
| Xóa không có xe | vehicles_count == 0 |
| Xóa có xe liên kết | vehicles_count > 0 → block |
| Tìm kiếm theo tên | q filter active |
| Lọc theo loại khách | customer_type_filter |

#### `test_vehicle.py`
**Mô tả**: Kiểm thử model và quản lý phương tiện
- Model Vehicle: unique constraints, status updates
- Views: CRUD operations và checkout bởi nhân viên

**Các test case chính**:
- ✅ Tạo phương tiện với validation biển số unique
- ✅ Thêm/sửa/xóa xe với form validation
- ✅ Checkout xe bởi nhân viên (in → out)
- ✅ Lọc và tìm kiếm theo các tiêu chí

| Test Case | Branch được cover |
|-----------|-----------------|
| Tạo phương tiện cơ bản | default values |
| Biển số trùng → IntegrityError | unique constraint |
| Không có khách hàng | null=True |
| Thêm xe hợp lệ | form.is_valid() = True |
| Biển số trùng → form lỗi | form.is_valid() = False |
| Thiếu biển số | required field |
| Checkout xe đang gửi | status == 'in' → checkout |
| Checkout xe đã ra | status == 'out' → no change |
| Xóa xe thành công | vehicle.delete() |
| Lọc theo khách tháng/vãng lai/tất cả | customer_type_filter |

#### `test_parking.py`
**Mô tả**: Kiểm thử check-in/out và models liên quan
- ParkingRecord: tính phí, fee calculation
- PricingSetting: get_price và fallback defaults
- Vehicle toggle parking: check-in/out bởi khách hàng

**Các test case chính**:
- ✅ Check-in xe vào bãi lần đầu
- ✅ Check-out xe có gói tháng (miễn phí)
- ✅ Check-out xe vãng lai (tính phí theo giờ)
- ✅ Kiểm tra xe chưa duyệt và quyền sở hữu

| Test Case | Branch được cover |
|-----------|-----------------|
| Tạo ParkingRecord | entry_time không null |
| `calculate_fee` không có exit_time → None | `not self.exit_time` |
| `calculate_fee` không có rate → None | `not self.parking_rate` |
| `PricingSetting.get_price` tìm thấy | active setting exists |
| `PricingSetting.get_price` không tìm thấy | DoesNotExist → default |
| `get_price` setting inactive | is_active=False → DoesNotExist |
| Giá mặc định cho mọi combo | defaults dict |
| Check-in xe vào bãi | active_record is None → vào |
| Check-out xe có gói tháng | current_subscription is not None |
| Check-out xe vãng lai | current_subscription is None |
| Xe chưa duyệt bị chặn | not vehicle.approved |
| Xe của người khác bị chặn | vehicle.customer != owner_obj |

#### `test_pricing.py`
**Mô tả**: Kiểm thử hệ thống bảng giá
- PricingSetting và PricingService models
- Admin pricing management views

**Các test case chính**:
- ✅ Tạo và cập nhật bảng giá
- ✅ Tính phí và fallback giá mặc định
- ✅ Validation giá và kiểm soát quyền truy cập admin
- ✅ Format giá theo định dạng tiền tệ

| Test Case | Branch được cover |
|-----------|-----------------|
| `PricingSetting.get_price` active | try → return pricing.price |
| `PricingSetting.get_price` not found | except DoesNotExist → defaults |
| Inactive setting → fallback | is_active=False → not found |
| Unknown combination → 0 | not in defaults dict |
| `PricingService.get_price` active | try → return price |
| `PricingService.get_price` not found | except → return 0 |
| `formatted_price()` | format với dấu phẩy |
| POST cập nhật giá | update_or_create |
| POST giá không hợp lệ | ValueError → continue |
| POST giá rỗng | value = '' → price = 0 |

### Cách chạy White-box Tests

> ⚠️ **Quan trọng**: Hệ thống dùng MySQL làm database chính. Test cần dùng SQLite để tách biệt. Thêm cấu hình sau vào settings hoặc tạo `tests/test_settings.py`:

#### Tạo file cấu hình test (`tests/test_settings.py`)
```python
from parking_management.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
```

#### Chạy tất cả white-box tests
```bash
# Dùng SQLite in-memory (khuyến nghị)
python manage.py test tests.whitebox_tests --settings=tests.test_settings

# Hoặc chạy từng module
python manage.py test tests.whitebox_tests.test_login --settings=tests.test_settings
python manage.py test tests.whitebox_tests.test_customer --settings=tests.test_settings
python manage.py test tests.whitebox_tests.test_vehicle --settings=tests.test_settings
python manage.py test tests.whitebox_tests.test_parking --settings=tests.test_settings
python manage.py test tests.whitebox_tests.test_pricing --settings=tests.test_settings
```

#### Chạy với coverage report
```bash
python -m pip install coverage
python -m coverage run --source='.' manage.py test tests.whitebox_tests --settings=tests.test_settings
python -m coverage report -m
python -m coverage html  # Tạo báo cáo HTML
```

---

## PHẦN 2: Selenium Testing

**Lưu ý**: Các file Selenium vẫn giữ comment bằng tiếng Anh để tương thích với chuẩn quốc tế của Selenium WebDriver.

### Yêu cầu cài đặt

```bash
pip install selenium
# Tải ChromeDriver phù hợp với phiên bản Chrome:
# https://chromedriver.chromium.org/downloads
```

### Cấu hình trước khi chạy

Trước khi chạy Selenium tests, cần:

1. **Khởi động server Django**:
   ```bash
   python manage.py runserver
   ```

2. **Tạo dữ liệu test** (nếu chưa có):
   ```bash
   python manage.py createsuperuser --username admin --email admin@test.com
   ```

3. **Cập nhật thông tin đăng nhập** trong mỗi file Selenium:
   ```python
   ADMIN_USERNAME = "your_admin_username"
   ADMIN_PASSWORD = "your_admin_password"
   ```

### Chi tiết từng file Selenium test

#### `selenium_login.py`
| Kịch bản | Mô tả |
|----------|-------|
| Admin login thành công | Redirect đến dashboard_admin |
| Login sai mật khẩu | Ở lại trang, có thông báo lỗi |
| Login form trống | Validation HTML5 / server-side |
| Username không tồn tại | Thông báo lỗi |
| User login sai mật khẩu | Ở lại trang user_login |
| User login form rỗng | Validation |

#### `selenium_customer.py`
| Kịch bản | Mô tả |
|----------|-------|
| Xem danh sách khách hàng | Trang load thành công |
| Thêm khách hàng hợp lệ | Form điền + submit → redirect |
| Tìm kiếm theo tên | Filter q= hoạt động |
| Thêm thiếu tên | Validation lỗi |

#### `selenium_vehicle.py`
| Kịch bản | Mô tả |
|----------|-------|
| Xem danh sách xe | Trang load thành công |
| Mở form thêm xe | Form có input plate_number |
| Thêm xe hợp lệ | Submit → redirect |
| Thêm xe thiếu biển số | Validation lỗi |
| Lọc theo loại khách | Filter customer_type= |
| Tìm kiếm theo biển số | Search q= |

#### `selenium_checkin_checkout.py`
| Kịch bản | Mô tả |
|----------|-------|
| Nhân viên xem xe đang gửi | Danh sách xe load |
| Nhân viên checkout xe | GET /vehicles/<pk>/checkout/ |
| Tìm nút checkout trong danh sách | Link href chứa 'checkout' |
| Khách hàng xem xe của mình | /customers/vehicles/ |
| Khách hàng toggle parking | Click nút vào/ra bãi |
| Khách hàng xem lịch sử | /customers/history/ |

#### `selenium_pricing.py`
| Kịch bản | Mô tả |
|----------|-------|
| Xem bảng giá | /parking/pricing/ load thành công |
| Admin xem cài đặt giá | /parking/admin/pricing/ có form |
| Admin cập nhật giá | POST với price_motorcycle_hourly |
| Admin nhập giá sai | Không crash, bỏ qua |
| Không phải admin → bị chặn | Redirect về login |

### Cách chạy Selenium Tests
Chạy server: python manage.py runserver

```bash
# Chạy từng file riêng lẻ
python manage.py test tests.selenium_tests.selenium_login --settings=tests.test_settings 
python manage.py test tests.selenium_tests.selenium_customer --settings=tests.test_settings 
python manage.py test tests.selenium_tests.selenium_vehicle --settings=tests.test_settings 
python manage.py test tests.selenium_tests.selenium_checkin_checkout --settings=tests.test_settings 

```

---

## PHẦN 3: Thống kê chức năng đã kiểm thử

| Chức năng | Whitebox | Selenium | Ghi chú |
|-----------|----------|----------|---------|
| Login (admin_login_view) | ✅ 7 tests | ✅ 4 tests | Đầy đủ |
| Login (login_view) | ✅ 8 tests | - | View login qua email |
| Login (user_login_view) | ✅ 7 tests | ✅ 2 tests | Email/username |
| Customer Model | ✅ 6 tests | - | Đầy đủ |
| Customer Add | ✅ 5 tests | ✅ 2 tests | Đầy đủ |
| Customer Edit | ✅ 4 tests | - | Đầy đủ |
| Customer Delete | ✅ 4 tests | - | Đầy đủ |
| Customer List/Search | ✅ 5 tests | ✅ 2 tests | Đầy đủ |
| Vehicle Model | ✅ 7 tests | - | Đầy đủ |
| Vehicle Form | ✅ 2 tests | - | Cơ bản |
| Vehicle Add | ✅ 5 tests | ✅ 3 tests | Đầy đủ |
| Vehicle Edit | ✅ 4 tests | - | Đầy đủ |
| Vehicle Checkout (nhân viên) | ✅ 3 tests | ✅ 3 tests | Đầy đủ |
| Vehicle List/Filter | ✅ 5 tests | ✅ 2 tests | Đầy đủ |
| ParkingRecord Model | ✅ 4 tests | - | Cơ bản |
| PricingSetting Model | ✅ 10 tests | - | Đầy đủ |
| PricingService Model | ✅ 7 tests | - | Đầy đủ |
| Check-in (toggle_parking) | ✅ 5 tests | ✅ 2 tests | Đầy đủ |
| Check-out với gói tháng | ✅ 1 test | - | Đầy đủ |
| Check-out vãng lai | ✅ 1 test | - | Đầy đủ |
| Pricing Views | ✅ 8 tests | ✅ 5 tests | Đầy đủ |

## PHẦN 5: Chức năng không thể test

Một số chức năng không thể test tự động do thiếu dữ liệu hoặc giao diện:

| Chức năng | Lý do không test được |
|-----------|----------------------|
| Upload ảnh phương tiện | Cần file image thực tế, không mock được trong unit test đơn giản |
| Export Excel (`/vehicles/export/`) | Cần kiểm tra nội dung file binary; cần thư viện openpyxl |
| Subscription check-in/out phức tạp | ParkingRecord yêu cầu Card và ParkingRate phải tồn tại (foreign key) |
| Wallet transactions | Cần flow thanh toán phức tạp với nhiều model |
| Salary management | Cần WorkShift active, logic phức tạp |
| QR Code vehicle | Cần thư viện generate QR và khách hàng có profile |
| Admin data cleaning views | Side effects khó kiểm soát trong test |
| Selenium toggle-parking | Cần xe đã approved trong DB của server test |

---

## Lưu ý kỹ thuật

### Database

Hệ thống dùng **MySQL** làm production database. Để chạy whitebox tests mà không cần MySQL:

```python
# tests/test_settings.py
from parking_management.settings import *
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
```

### Signal trong vehicles/models.py

Model `Vehicle` có `post_save` signal tự động tạo `PaymentTransaction` khi khách **gửi tháng**. Các test dùng khách **vãng lai** để tránh phụ thuộc không cần thiết.

### Selenium ChromeDriver

- Tải ChromeDriver phù hợp với phiên bản Chrome: https://chromedriver.chromium.org/
- Đặt vào PATH hoặc chỉ định đường dẫn trong code
- Chạy headless bằng cách bỏ comment `options.add_argument("--headless")`
