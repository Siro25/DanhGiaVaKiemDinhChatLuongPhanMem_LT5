# Báo cáo Kiểm thử – Django Parking Management System

## 1. Các File Đã Tạo

### White-box Tests (`tests/whitebox_tests/`)

| File | Số test | Mô tả |
|------|---------|-------|
| [test_login.py](file:///d:/Pro/DanhGiaVaKiemDinh/DanhGiaVaKiemDinh/tests/whitebox_tests/test_login.py) | **22 tests** | LoginForm, login_view, admin_login_view, user_login_view |
| [test_customer.py](file:///d:/Pro/DanhGiaVaKiemDinh/DanhGiaVaKiemDinh/tests/whitebox_tests/test_customer.py) | **24 tests** | Customer model, Add/Edit/Delete/List/Detail views |
| [test_vehicle.py](file:///d:/Pro/DanhGiaVaKiemDinh/DanhGiaVaKiemDinh/tests/whitebox_tests/test_vehicle.py) | **26 tests** | Vehicle model, Form, Add/Edit/Checkout/Delete/List views |
| [test_parking.py](file:///d:/Pro/DanhGiaVaKiemDinh/DanhGiaVaKiemDinh/tests/whitebox_tests/test_parking.py) | **21 tests** | ParkingRecord, PricingSetting, ParkingLot, toggle_parking, checkout |
| [test_pricing.py](file:///d:/Pro/DanhGiaVaKiemDinh/DanhGiaVaKiemDinh/tests/whitebox_tests/test_pricing.py) | **25 tests** | PricingSetting, PricingService, pricing_list, admin_pricing_settings |
| **Tổng cộng** | **118 tests** | |

### Selenium Tests (`tests/selenium_tests/`)

| File | Số kịch bản | Mô tả |
|------|-------------|-------|
| [selenium_login.py](file:///d:/Pro/DanhGiaVaKiemDinh/DanhGiaVaKiemDinh/tests/selenium_tests/selenium_login.py) | 6 kịch bản | Admin login, User login, sai mật khẩu, form trống |
| [selenium_customer.py](file:///d:/Pro/DanhGiaVaKiemDinh/DanhGiaVaKiemDinh/tests/selenium_tests/selenium_customer.py) | 4 kịch bản | Xem danh sách, thêm, tìm kiếm, validation |
| [selenium_vehicle.py](file:///d:/Pro/DanhGiaVaKiemDinh/DanhGiaVaKiemDinh/tests/selenium_tests/selenium_vehicle.py) | 6 kịch bản | Xem danh sách, thêm, filter, tìm kiếm |
| [selenium_checkin_checkout.py](file:///d:/Pro/DanhGiaVaKiemDinh/DanhGiaVaKiemDinh/tests/selenium_tests/selenium_checkin_checkout.py) | 6 kịch bản | Checkout (nhân viên), Toggle parking (khách hàng) |
| [selenium_pricing.py](file:///d:/Pro/DanhGiaVaKiemDinh/DanhGiaVaKiemDinh/tests/selenium_tests/selenium_pricing.py) | 5 kịch bản | Xem bảng giá, admin cập nhật giá, validation, access control |
| **Tổng cộng** | **27 kịch bản** | |

### File hỗ trợ

| File | Mô tả |
|------|-------|
| [tests/test_settings.py](file:///d:/Pro/DanhGiaVaKiemDinh/DanhGiaVaKiemDinh/tests/test_settings.py) | Django settings dùng SQLite in-memory cho test |
| [tests/README.md](file:///d:/Pro/DanhGiaVaKiemDinh/DanhGiaVaKiemDinh/tests/README.md) | Tài liệu hướng dẫn đầy đủ |

---

## 2. Thống kê Branch Coverage

### accounts/views.py – `login_view`

```
if email:                          ← ✅ True (email có), False (email rỗng)
  if user_obj is not None:         ← ✅ True (tìm thấy), False (không tìm thấy)
    if user is not None:           ← ✅ True (auth thành công), False (sai pass)
      if user.role == 'nhanvien':  ← ✅ True, False
        if user.status != 'approved': ← ✅ True (pending/rejected), False (approved)
          if user.status == 'pending': ← ✅ True, False
        if user.role == 'admin':   ← ✅ True, False
        elif user.role == 'nhanvien': ← ✅ True, False
        elif user.role == 'khachhang': ← ✅ True, False
```

### accounts/views.py – `admin_login_view`

```
if not username or not password:   ← ✅ True (trống), False (có giá trị)
if user is not None:               ← ✅ True (auth ok), False (sai pass/không tồn tại)
  if user.role == 'admin':         ← ✅ True (admin), False (không phải admin)
```

### customers/views.py – `customer_add`

```
if name and phone:                 ← ✅ True (có cả hai), False (thiếu một)
  if request.user.role == 'admin': ← ✅ True, False
```

### customers/views.py – `customer_delete`

```
if request.method == 'POST':       ← ✅ GET (confirm), POST (xóa)
  if vehicles_count > 0:           ← ✅ True (có xe → block), False (không xe → xóa)
  if transactions_count > 0:       ← ✅ True, False
  if request.user.role == 'admin': ← ✅ True, False (redirect khác nhau)
```

### vehicles/views.py – `vehicle_checkout`

```
if vehicle.status == 'in':         ← ✅ True (checkout), False (không làm gì)
```

### customers/views.py – `vehicle_toggle_parking`

```
if vehicle.customer != owner_obj:  ← ✅ True (block), False (tiếp tục)
if not vehicle.approved:           ← ✅ True (block), False (tiếp tục)
if active_record:                  ← ✅ True (checkout), False (check-in)
  if current_subscription:         ← ✅ True (miễn phí), False (tính phí)
```

### parking/models.py – `PricingSetting.get_price`

```
try:
  pricing = cls.objects.get(...)   ← ✅ Tìm thấy active → return price
except cls.DoesNotExist:           ← ✅ Không tìm thấy / inactive → defaults
  return defaults.get(..., 0)      ← ✅ Có trong defaults, không có → 0
```

### parking/views.py – `admin_pricing_settings`

```
if request.method == 'POST':       ← ✅ GET (hiển thị), POST (cập nhật)
  if key.startswith('price_'):     ← ✅ True, False
    if len(parts) == 3:            ← ✅ True (valid key format), False
      try:
        price = float(value)       ← ✅ Hợp lệ
      except (ValueError, TypeError): ← ✅ Giá trị không phải số → continue
```

---

## 3. Thống kê Chức năng Được Kiểm thử

| Chức năng | Whitebox ✅ | Selenium ✅ | Trạng thái |
|-----------|-----------|-----------|-----------|
| Login (admin) | ✅ | ✅ | Đầy đủ |
| Login (nhân viên) | ✅ | - | Đầy đủ |
| Login (khách hàng) | ✅ | ✅ | Đầy đủ |
| Signup | - | - | Chưa test |
| Customer Model | ✅ | - | Đầy đủ |
| Customer Add | ✅ | ✅ | Đầy đủ |
| Customer Edit | ✅ | - | Đầy đủ |
| Customer Delete | ✅ | - | Đầy đủ |
| Customer List/Search | ✅ | ✅ | Đầy đủ |
| Vehicle Model | ✅ | - | Đầy đủ |
| Vehicle Add | ✅ | ✅ | Đầy đủ |
| Vehicle Edit | ✅ | - | Đầy đủ |
| Vehicle Checkout | ✅ | ✅ | Đầy đủ |
| Vehicle Delete | ✅ | - | Đầy đủ |
| Vehicle List/Filter | ✅ | ✅ | Đầy đủ |
| Check-in (khách hàng) | ✅ | ✅ | Đầy đủ |
| Check-out có gói tháng | ✅ | - | Đầy đủ |
| Check-out vãng lai | ✅ | - | Đầy đủ |
| PricingSetting | ✅ | - | Đầy đủ |
| PricingService | ✅ | - | Đầy đủ |
| Pricing List View | ✅ | ✅ | Đầy đủ |
| Admin Pricing Settings | ✅ | ✅ | Đầy đủ |

---

## 4. Chức năng Không Thể Test

> [!WARNING]
> Các chức năng sau không được test tự động do thiếu hạ tầng hoặc phụ thuộc phức tạp.

| Chức năng | Lý do |
|-----------|-------|
| `export_vehicles_excel` | Cần kiểm tra binary file, phụ thuộc openpyxl |
| `export_customers_excel` | Tương tự |
| Upload ảnh xe (`image`) | Cần multipart form data với file thực tế |
| `vehicle_qr` | Cần QR library và customer có user |
| Wallet transactions | Flow phức tạp với nhiều model |
| Salary management | Cần WorkShift active |
| Admin data cleaning | Side effects khó kiểm soát |
| `signup_view` | Tạo Customer profile + User phức tạp |
| ParkingRecord trong blackbox | ForeignKey tới Card và ParkingRate bắt buộc |

> [!NOTE]
> `ParkingRecord.calculate_fee()` chỉ test được một phần do `ParkingRate` không có field `rate_type` và `rate` thực tế – chỉ có `hourly_rate`, `daily_rate`, `monthly_rate`.

---

## 5. Cách Chạy Test

### Whitebox Tests

```bash
# Cài đặt
python -m pip install coverage

# Chạy tất cả
python manage.py test tests.whitebox_tests --settings=tests.test_settings

# Chạy với coverage
python -m coverage run --source='.' manage.py test tests.whitebox_tests --settings=tests.test_settings
python -m coverage report -m
python -m coverage html
```

### Selenium Tests

```bash
# Bước 1: Khởi động server
python manage.py runserver

# Bước 2: Chạy từng file
python tests/selenium_tests/selenium_login.py
python tests/selenium_tests/selenium_customer.py
python tests/selenium_tests/selenium_vehicle.py
python tests/selenium_tests/selenium_checkin_checkout.py
python tests/selenium_tests/selenium_pricing.py
```
