# Parking Management System Testing Documentation

## Tổng quan

Tài liệu này mô tả toàn bộ hệ thống kiểm thử của **Parking Management System**, bao gồm:

* White-box Testing sử dụng Django TestCase
* Automated UI Testing sử dụng Selenium WebDriver
* Hướng dẫn cấu hình môi trường kiểm thử
* Danh sách chức năng đã được kiểm thử
* Các hạn chế và chức năng chưa thể tự động hóa

---

# Cấu trúc thư mục

```text
tests/
├── whitebox_tests/
│   ├── test_login.py
│   ├── test_customer.py
│   ├── test_vehicle.py
│   ├── test_parking.py
│   └── test_pricing.py
│
├── selenium_tests/
│   ├── selenium_login.py
│   ├── selenium_customer.py
│   ├── selenium_vehicle.py
│   ├── selenium_checkin_checkout.py
│   └── selenium_pricing.py
│
└── README.md
```

---

# 1. White-box Testing

## Mục tiêu

Bộ kiểm thử White-box được xây dựng bằng Django TestCase nhằm đánh giá tính đúng đắn của:

* Models
* Views
* Business Logic
* Validation Rules
* Permission Control

### Tiêu chí bao phủ mã nguồn

| Tiêu chí           | Mô tả                                                |
| ------------------ | ---------------------------------------------------- |
| Statement Coverage | Mỗi câu lệnh được thực thi ít nhất một lần           |
| Branch Coverage    | Mọi nhánh điều kiện được kiểm tra                    |
| Condition Coverage | Mọi biểu thức Boolean được đánh giá cả True và False |

---

## test_login.py

Kiểm thử các chức năng xác thực người dùng:

* login_view
* admin_login_view
* user_login_view

### Nội dung kiểm thử

* Đăng nhập thành công
* Sai mật khẩu
* Email không tồn tại
* Tài khoản nhân viên đang chờ duyệt
* Tài khoản bị từ chối
* Form không hợp lệ
* Safe Redirect

---

## test_customer.py

Kiểm thử chức năng quản lý khách hàng.

### Nội dung kiểm thử

* Tạo khách hàng
* Cập nhật thông tin
* Xóa khách hàng
* Validation dữ liệu
* Tìm kiếm khách hàng
* Lọc theo loại khách

---

## test_vehicle.py

Kiểm thử quản lý phương tiện.

### Nội dung kiểm thử

* Tạo phương tiện
* Kiểm tra biển số duy nhất
* Thêm, sửa, xóa xe
* Checkout phương tiện
* Tìm kiếm và lọc dữ liệu

---

## test_parking.py

Kiểm thử nghiệp vụ gửi xe.

### Nội dung kiểm thử

* Check-in
* Check-out
* Tính phí gửi xe
* Gói gửi tháng
* Kiểm tra quyền sở hữu xe
* Xác thực xe đã được duyệt

---

## test_pricing.py

Kiểm thử hệ thống bảng giá.

### Nội dung kiểm thử

* Tạo bảng giá
* Cập nhật giá
* Fallback giá mặc định
* Validation dữ liệu
* Phân quyền quản trị viên
* Định dạng hiển thị tiền tệ

---

# Chạy White-box Tests

## Tạo cấu hình SQLite cho môi trường test

```python
from parking_management.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
```

Lưu thành:

```text
tests/test_settings.py
```

## Chạy toàn bộ test

```bash
python manage.py test tests.whitebox_tests --settings=tests.test_settings
```

## Chạy từng module

```bash
python manage.py test tests.whitebox_tests.test_login --settings=tests.test_settings

python manage.py test tests.whitebox_tests.test_customer --settings=tests.test_settings

python manage.py test tests.whitebox_tests.test_vehicle --settings=tests.test_settings

python manage.py test tests.whitebox_tests.test_parking --settings=tests.test_settings

python manage.py test tests.whitebox_tests.test_pricing --settings=tests.test_settings
```

---

## Báo cáo Coverage

Cài đặt:

```bash
pip install coverage
```

Thực thi:

```bash
coverage run --source='.' manage.py test tests.whitebox_tests --settings=tests.test_settings
coverage report -m
coverage html
```

Báo cáo HTML sẽ được tạo trong thư mục:

```text
htmlcov/
```

---

# 2. Selenium Testing

## Mục tiêu

Kiểm thử giao diện và luồng thao tác thực tế của người dùng trên trình duyệt.

### Công nghệ sử dụng

* Selenium WebDriver
* Google Chrome
* ChromeDriver

---

## Cài đặt

```bash
pip install selenium
```

Tải ChromeDriver phù hợp với phiên bản Chrome đang sử dụng.

---

## Chuẩn bị môi trường

Khởi động server:

```bash
python manage.py runserver
```

Tạo tài khoản quản trị:

```bash
python manage.py createsuperuser
```

Cập nhật thông tin đăng nhập trong các file Selenium:

```python
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password"
```

---

## Các bộ kiểm thử Selenium

### selenium_login.py

* Đăng nhập thành công
* Sai mật khẩu
* Form rỗng
* Username không tồn tại

### selenium_customer.py

* Xem danh sách khách hàng
* Thêm khách hàng
* Tìm kiếm khách hàng
* Kiểm tra validation

### selenium_vehicle.py

* Xem danh sách xe
* Thêm xe mới
* Tìm kiếm xe
* Lọc theo loại khách

### selenium_checkin_checkout.py

* Theo dõi xe đang gửi
* Checkout xe
* Kiểm tra lịch sử gửi xe
* Toggle trạng thái vào/ra bãi

### selenium_pricing.py

* Xem bảng giá
* Quản lý giá dịch vụ
* Cập nhật giá
* Kiểm tra phân quyền

---

## Chạy Selenium Tests

```bash
python manage.py test tests.selenium_tests.selenium_login

python manage.py test tests.selenium_tests.selenium_customer

python manage.py test tests.selenium_tests.selenium_vehicle

python manage.py test tests.selenium_tests.selenium_checkin_checkout

python manage.py test tests.selenium_tests.selenium_pricing
```

---

# Chức năng đã được kiểm thử

Các nhóm chức năng chính đã được bao phủ:

* Authentication & Authorization
* Customer Management
* Vehicle Management
* Parking Check-in / Check-out
* Pricing Management
* Parking Record Processing
* Search & Filtering
* Permission Control

---

# Các chức năng chưa tự động hóa

| Chức năng              | Nguyên nhân                       |
| ---------------------- | --------------------------------- |
| Upload ảnh phương tiện | Phụ thuộc file ảnh thực           |
| Export Excel           | Cần kiểm tra dữ liệu file sinh ra |
| QR Code Vehicle        | Phụ thuộc thư viện QR             |
| Wallet Transaction     | Nghiệp vụ phức tạp                |
| Salary Management      | Phụ thuộc nhiều model             |
| Subscription nâng cao  | Yêu cầu dữ liệu liên kết phức tạp |

---

# Lưu ý kỹ thuật

## Database

Môi trường Production sử dụng MySQL.

Môi trường Test sử dụng SQLite In-Memory để:

* Tăng tốc độ thực thi
* Không ảnh hưởng dữ liệu thật
* Dễ triển khai CI/CD

## Vehicle Signal

Model Vehicle có signal tự động tạo PaymentTransaction khi khách gửi tháng.

Để tránh phụ thuộc không cần thiết, các test sử dụng khách hàng vãng lai làm dữ liệu mặc định.

## ChromeDriver

ChromeDriver phải tương thích với phiên bản Google Chrome hiện tại.

Có thể chạy chế độ headless bằng cách bật:

```python
options.add_argument("--headless")
```
