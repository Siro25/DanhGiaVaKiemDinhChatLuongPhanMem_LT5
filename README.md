# 🚗 Hệ Thống Quản Lý Bãi Đỗ Xe

[![Django](https://img.shields.io/badge/Django-5.2.6-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Hệ thống quản lý bãi đỗ xe thông minh được phát triển bằng Django Framework, hỗ trợ quản lý xe vãng lai và gói đăng ký tháng.

## 📋 Mục Lục

- [Tính Năng](#-tính-năng)
- [Công Nghệ Sử Dụng](#-công-nghệ-sử-dụng)
- [Cài Đặt](#-cài-đặt)
- [Cấu Trúc Dự Án](#-cấu-trúc-dự-án)
- [Sử Dụng](#-sử-dụng)
- [Phân Quyền](#-phân-quyền)
- [API Endpoints](#-api-endpoints)
- [Đóng Góp](#-đóng-góp)
- [Tác Giả](#-tác-giả)

## ✨ Tính Năng

### 🔐 Quản Lý Tài Khoản & Phân Quyền
- **3 loại tài khoản:** Admin, Nhân viên, Khách hàng
- Đăng ký, đăng nhập, đăng xuất
- Quản lý hồ sơ cá nhân
- Xác thực và phân quyền đa cấp

### 🚙 Quản Lý Xe
- Đăng ký xe với nhiều loại: Ô tô, Xe máy, Xe đạp, Xe tải, Taxi
- Duyệt/từ chối xe bởi Admin/Nhân viên
- Theo dõi trạng thái xe (đang trong bãi/đã ra)
- Lịch sử ra/vào của từng xe
- Hỗ trợ nhiều xe cho một khách hàng

### 💳 Gói Đăng Ký Tháng
- Đăng ký gói tháng cho **từng xe cụ thể**
- Tính phí theo loại xe và thời hạn (1, 3, 6, 12 tháng)
- Miễn phí ra/vào cho xe có gói tháng còn hiệu lực
- Theo dõi ngày hết hạn và cảnh báo sắp hết hạn (≤ 7 ngày)
- Gia hạn gói tháng tự động

### 💰 Quản Lý Ví & Thanh Toán
- Ví điện tử cho mỗi khách hàng
- Nạp tiền vào ví
- Thanh toán gói tháng từ ví
- Lịch sử giao dịch chi tiết
- Hiển thị số dư và biến động

### 🅿️ Quản Lý Bãi Đỗ Xe
- Quản lý nhiều bãi xe
- Theo dõi sức chứa và số chỗ trống
- Ghi nhận thời gian vào/ra
- Tính phí tự động theo giờ (cho xe vãng lai)
- Miễn phí cho xe gói tháng

### 📊 Báo Cáo & Thống Kê
- Thống kê doanh thu theo ngày/tháng/năm
- Báo cáo số lượng xe vào/ra
- Phân tích theo loại xe
- Báo cáo khách hàng gửi tháng vs vãng lai
- Xuất báo cáo chi tiết

### 💵 Bảng Giá Linh Hoạt
- Thiết lập giá theo loại xe
- Giá theo giờ (hourly) và theo tháng (monthly)
- Cập nhật bảng giá bởi Admin
- Áp dụng giá khác nhau cho từng loại xe

### 📱 Giao Diện Người Dùng
- Responsive design với Bootstrap 5
- Dashboard riêng cho từng loại người dùng
- Thông báo realtime
- Icon trực quan với Bootstrap Icons
- Màu sắc phân loại theo trạng thái

## 🛠 Công Nghệ Sử Dụng

### Backend
- **Framework:** Django 5.2.6
- **Database:** SQLite3 (Development) / PostgreSQL (Production)
- **Authentication:** Django Auth System
- **ORM:** Django ORM

### Frontend
- **CSS Framework:** Bootstrap 5
- **Icons:** Bootstrap Icons
- **JavaScript:** Vanilla JS
- **Template Engine:** Django Templates

### Các Thư Viện Chính
- `django-crispy-forms` - Form rendering
- `Pillow` - Xử lý hình ảnh
- `python-dateutil` - Xử lý ngày tháng

## 📦 Cài Đặt

### Yêu Cầu Hệ Thống
- Python 3.8 trở lên
- pip (Python package manager)
- Git

### Các Bước Cài Đặt

1. **Clone Repository**
```bash
git clone https://github.com/ChiNguyenxK5/PhanTichVaThietKePhanMemNO1_Nhom14.git
cd PhanTichVaThietKePhanMemNO1_Nhom14
```

2. **Tạo Virtual Environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Cài Đặt Dependencies**
```bash
pip install django pillow python-dateutil django-crispy-forms crispy-bootstrap5
```

4. **Tạo File Requirements** (tùy chọn)
```bash
pip freeze > requirements.txt
```

5. **Chạy Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Tạo Superuser (Admin)**
```bash
python manage.py init_admin
python manage.py init_roles
```

7. **Khởi Động Server**
```bash
python manage.py runserver
```

8. **Truy Cập Ứng Dụng**
- Website: http://127.0.0.1:8000/
- Admin Panel: http://127.0.0.1:8000/admin/

## 📁 Cấu Trúc Dự Án

```
PhanTichVaThietKePhanMemNO1_Nhom14/
│
├── accounts/              # Quản lý tài khoản & authentication
│   ├── models.py          # Custom User model
│   ├── views.py           # Login, logout, register
│   └── urls.py
│
├── customers/             # Quản lý khách hàng
│   ├── models.py          # Customer, MonthlySubscription, Wallet
│   ├── views.py           # Customer dashboard, vehicle management
│   ├── subscription_views.py  # Đăng ký gói tháng
│   ├── wallet_views.py    # Quản lý ví
│   └── templatetags/      # Custom template filters
│
├── vehicles/              # Quản lý xe
│   ├── models.py          # Vehicle model
│   ├── views.py           # CRUD operations
│   └── admin.py           # Admin interface
│
├── parking/               # Quản lý bãi xe
│   ├── models.py          # ParkingLot, ParkingRecord
│   ├── views.py           # Vào/ra bãi, tính phí
│   └── admin.py
│
├── cards/                 # Quản lý thẻ & thanh toán
│   ├── models.py          # Card, PaymentTransaction
│   └── views.py
│
├── pricing/               # Quản lý bảng giá
│   ├── models.py          # PricingSetting
│   ├── views.py           # CRUD pricing
│   └── admin.py
│
├── finance/               # Quản lý tài chính
│   ├── models.py          # Transaction records
│   └── views.py
│
├── reports/               # Báo cáo & thống kê
│   ├── views.py           # Revenue, statistics
│   └── templates/
│
├── templates/             # Django templates
│   ├── base.html          # Base template
│   ├── accounts/          # Login, register templates
│   ├── customers/         # Customer templates
│   ├── parking/           # Parking templates
│   └── reports/           # Report templates
│
├── static/                # Static files
│   ├── css/
│   ├── js/
│   └── images/
│
├── parking_management/    # Project settings
│   ├── settings.py        # Django settings
│   ├── urls.py            # Root URLs
│   └── wsgi.py
│
├── manage.py              # Django management script
└── db.sqlite3             # SQLite database
```

## 🎯 Sử Dụng

### 1. Tài Khoản Admin

**Truy cập Admin Panel:**
- URL: `/admin/`
- Đăng nhập bằng superuser đã tạo

**Chức năng:**
- ✅ Quản lý tất cả users (Admin, Nhân viên, Khách hàng)
- ✅ Duyệt/từ chối đăng ký xe
- ✅ Cập nhật bảng giá
- ✅ Quản lý bãi xe
- ✅ Xem báo cáo doanh thu
- ✅ Quản lý gói đăng ký tháng

### 2. Tài Khoản Nhân Viên

**Dashboard:** `/staff/dashboard/`

**Chức năng:**
- ✅ Duyệt đăng ký xe
- ✅ Quản lý xe ra/vào bãi
- ✅ Xem thông tin khách hàng
- ✅ Xử lý thanh toán
- ⛔ Không được thay đổi bảng giá

### 3. Tài Khoản Khách Hàng

**Dashboard:** `/customers/dashboard/`

**Chức năng:**
- ✅ Đăng ký xe mới
- ✅ Xem danh sách xe của mình
- ✅ Đăng ký/gia hạn gói tháng **cho từng xe**
- ✅ Quản lý ví (nạp tiền, xem lịch sử)
- ✅ Theo dõi lịch sử ra/vào bãi
- ✅ Xem trạng thái gói tháng từng xe
- ✅ Nhận cảnh báo gói sắp hết hạn

### 4. Quy Trình Sử Dụng

#### Đăng Ký Xe Mới
1. Khách hàng đăng nhập
2. Vào "Xe của tôi" → "Đăng ký xe mới"
3. Điền thông tin: Biển số, loại xe, màu sắc
4. Chờ Admin/Nhân viên duyệt

#### Đăng Ký Gói Tháng
1. Vào "Gói tháng" → "Đăng ký gói tháng"
2. **Chọn xe cụ thể** từ dropdown
3. Chọn thời hạn (1/3/6/12 tháng)
4. Xác nhận thanh toán từ ví
5. Nhận thông báo thành công với ngày hết hạn

#### Vào/Ra Bãi Xe
1. Khách hàng vào "Xe của tôi"
2. Click nút "Vào bãi" hoặc "Ra bãi"
3. Hệ thống tự động:
   - Kiểm tra gói tháng của **xe cụ thể đó**
   - Nếu có gói còn hiệu lực → **Miễn phí**
   - Nếu không có gói → Tính phí theo giờ

## 🔒 Phân Quyền

| Chức Năng | Admin | Nhân Viên | Khách Hàng |
|-----------|-------|-----------|------------|
| Quản lý users | ✅ | ⛔ | ⛔ |
| Duyệt xe | ✅ | ✅ | ⛔ |
| Cập nhật giá | ✅ | ⛔ | ⛔ |
| Đăng ký xe | ✅ | ✅ | ✅ |
| Đăng ký gói tháng | ⛔ | ⛔ | ✅ |
| Quản lý ví | ⛔ | ⛔ | ✅ |
| Xem báo cáo | ✅ | ✅ | ⛔ |
| Vào/ra bãi | ✅ | ✅ | ✅ |

## 🔌 API Endpoints

### Accounts
```
POST   /accounts/login/           # Đăng nhập
POST   /accounts/register/        # Đăng ký
GET    /accounts/logout/          # Đăng xuất
GET    /accounts/profile/         # Xem profile
```

### Customers
```
GET    /customers/dashboard/      # Dashboard khách hàng
GET    /customers/vehicles/       # Danh sách xe
POST   /customers/vehicles/add/   # Thêm xe mới
GET    /customers/history/        # Lịch sử
POST   /customers/subscribe/      # Đăng ký gói tháng
GET    /customers/wallet/         # Quản lý ví
POST   /customers/wallet/deposit/ # Nạp tiền
```

### Parking
```
POST   /parking/vehicle/{id}/toggle/  # Vào/ra bãi
GET    /parking/lots/                 # Danh sách bãi
GET    /parking/records/              # Lịch sử ra/vào
```

### Pricing
```
GET    /pricing/                  # Xem bảng giá
POST   /pricing/update/          # Cập nhật giá (Admin)
```

### Reports
```
GET    /reports/revenue/         # Báo cáo doanh thu
GET    /reports/statistics/      # Thống kê
```

## 🎨 Screenshots

### Dashboard Khách Hàng
- Tổng quan số xe, gói tháng, số dư ví
- Danh sách xe với trạng thái gói tháng rõ ràng
- Thông báo gói sắp hết hạn

### Trang Lịch Sử
- **Card hiển thị từng xe** với thông tin gói tháng:
  - ✅ Gói đang hoạt động (màu xanh) + số ngày còn lại
  - ⚠️ Sắp hết hạn (màu vàng)
  - ❌ Đã hết hạn (màu đỏ) + nút gia hạn
  - ℹ️ Chưa có gói (màu xám) + nút đăng ký

- Bảng lịch sử ra/vào với cột "Gói tháng"

## 🧪 Testing

```bash
# Chạy tất cả tests
python manage.py test

# Test một app cụ thể
python manage.py test customers
python manage.py test vehicles

# Test với coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 🚀 Deployment

### Production Settings

1. **Cập nhật settings.py:**
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
```

2. **Sử dụng PostgreSQL:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'parking_db',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

3. **Collect Static Files:**
```bash
python manage.py collectstatic
```

4. **Deploy với Gunicorn:**
```bash
pip install gunicorn
gunicorn parking_management.wsgi:application
```

## 📝 Database Schema

### Các Model Chính

**Customer**
- user (OneToOne → User)
- name, phone, email, address
- customer_type: "Khách vãng lai" / "Khách gửi tháng"
- status: not_registered / awaiting_approval / approved

**Vehicle**
- customer (ForeignKey → Customer)
- plate_number (unique)
- vehicle_type: car / motorcycle / bicycle / truck / taxi
- color
- approved (Boolean)
- check_in (DateTime) - trạng thái trong/ngoài bãi

**MonthlySubscription**
- customer (ForeignKey → Customer)
- **vehicle (ForeignKey → Vehicle)** - Gói tháng gắn với xe cụ thể
- start_date, end_date
- is_active (Boolean)

**Wallet**
- customer (OneToOne → Customer)
- balance (Decimal)

**ParkingRecord**
- vehicle (ForeignKey → Vehicle)
- parking_lot (ForeignKey → ParkingLot)
- entry_time, exit_time
- fee (Decimal)
- is_paid (Boolean)

**PricingSetting**
- vehicle_type: car / motorcycle / bicycle / truck / taxi
- package_type: hourly / monthly
- price (Decimal)

## 🤝 Đóng Góp

Chúng tôi hoan nghênh mọi đóng góp! Vui lòng:

1. Fork repository
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 👥 Tác Giả

**Nhóm 14 - Phân Tích và Thiết Kế Phần Mềm NO1**
- Thành viên : Nguyễn Duy Anh Tuấn , Nguyễn Mạnh Chí , Đỗ Tiến Sĩ
- GitHub: [@ChiNguyenxK5](https://github.com/ChiNguyenxK5)
- Repository: [PhanTichVaThietKePhanMemNO1_Nhom14](https://github.com/ChiNguyenxK5/PhanTichVaThietKePhanMemNO1_Nhom14)

## 📞 Liên Hệ

Nếu có bất kỳ câu hỏi hoặc góp ý nào, vui lòng:
- Tạo Issue trên GitHub
- Hoặc liên hệ qua email

## 🙏 Lời Cảm Ơn

- Django Documentation
- Bootstrap Team
- Bootstrap Icons
- Tất cả contributors

---

**Made with ❤️ by Nhóm 14**
