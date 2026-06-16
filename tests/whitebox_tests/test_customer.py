"""Unit tests white-box cho chức năng quản lý khách hàng (Customer Management)."""

from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from customers.models import Customer


def create_staff(username="staffuser", password="staffpass!"):
    """Tạo nhân viên (nhanvien) để thực hiện thao tác quản lý khách hàng."""
    return User.objects.create_user(
        username=username, password=password, email=f"{username}@test.com",
        role="nhanvien", status="approved"
    )

def create_customer(name="Nguyễn Văn A", phone="0901234567", customer_type="Khách vãng lai", **kwargs):
    """Tạo Customer nhanh."""
    return Customer.objects.create(name=name, phone=phone, customer_type=customer_type, **kwargs)


class CustomerModelTests(TestCase):
    """Kiểm tra model Customer: tạo, validation, str representation."""
    
    def test_01_customer_model_creation_and_defaults(self):
        """Tạo Customer cơ bản và kiểm tra defaults, str method."""
        # Kiểm tra tạo customer cơ bản
        customer = create_customer("Trần Văn B", "0912345678", "Khách gửi tháng")
        self.assertEqual(customer.name, "Trần Văn B")
        self.assertEqual(customer.phone, "0912345678")
        self.assertEqual(customer.customer_type, "Khách gửi tháng")
        self.assertEqual(customer.status, "not_registered")  # mặc định
        self.assertTrue(customer.is_active)  # mặc định
        
        # Kiểm tra __str__ method có tên và số điện thoại
        str_repr = str(customer)
        self.assertIn("Trần Văn B", str_repr)
        self.assertIn("0912345678", str_repr)
        
        # Kiểm tra customer có trường email
        customer_with_email = Customer.objects.create(
            name="Email Test", phone="0900000001", email="test@email.com", customer_type="Khách vãng lai"
        )
        self.assertEqual(customer_with_email.email, "test@email.com")


class CustomerCRUDViewTests(TestCase):
    """Kiểm tra các thao tác CRUD: thêm, sửa, xóa khách hàng."""
    
    def setUp(self):
        self.client = Client()
        self.staff = create_staff()
        self.client.force_login(self.staff)
    
    def test_02_customer_add_success_and_validation(self):
        """Kiểm tra thêm khách hàng thành công và validation."""
        # Kiểm tra thêm thành công cho cả hai loại khách hàng
        add_url = reverse("customers:customer_add")
        
        # Khách vãng lai hợp lệ
        guest_data = {"name": "Khách Vãng Lai", "phone": "0901111111", 
                     "customer_type": "Khách vãng lai", "email": "", "address": ""}
        response = self.client.post(add_url, guest_data)
        self.assertEqual(response.status_code, 302)  # redirect khi thành công
        self.assertTrue(Customer.objects.filter(name="Khách Vãng Lai").exists())
        
        # Khách gửi tháng hợp lệ với thông tin đầy đủ
        monthly_data = {"name": "Khách Tháng", "phone": "0902222222", 
                       "customer_type": "Khách gửi tháng", "email": "thang@test.com", "address": "123 ABC"}
        response = self.client.post(add_url, monthly_data)
        self.assertEqual(response.status_code, 302)
        monthly_customer = Customer.objects.get(name="Khách Tháng")
        self.assertEqual(monthly_customer.created_by, self.staff)
        
        # Kiểm tra validation: thiếu trường bắt buộc
        invalid_data = {"name": "", "phone": "0903333333", "customer_type": "Khách vãng lai"}
        response = self.client.post(add_url, invalid_data)
        self.assertEqual(response.status_code, 200)  # ở lại form
        self.assertFalse(Customer.objects.filter(phone="0903333333").exists())
    
    def test_03_customer_edit_and_update(self):
        """Kiểm tra sửa thông tin khách hàng."""
        customer = create_customer("Original Name", "0904444444")
        edit_url = reverse("customers:customer_edit", kwargs={"pk": customer.pk})
        
        # Kiểm tra cập nhật thành công
        update_data = {"name": "Updated Name", "phone": "0904444445", 
                      "customer_type": "Khách vãng lai", "email": "updated@test.com"}
        response = self.client.post(edit_url, update_data)
        self.assertEqual(response.status_code, 302)
        customer.refresh_from_db()
        self.assertEqual(customer.name, "Updated Name")
        self.assertEqual(customer.phone, "0904444445")
        
        # Kiểm tra validation khi sửa: thiếu tên
        invalid_data = {"name": "", "phone": "0904444444", "customer_type": "Khách vãng lai"}
        response = self.client.post(edit_url, invalid_data)
        self.assertEqual(response.status_code, 200)  # ở lại form
        customer.refresh_from_db()
        self.assertEqual(customer.name, "Updated Name")  # không thay đổi
        
        # Kiểm tra 404 cho khách hàng không tồn tại
        invalid_url = reverse("customers:customer_edit", kwargs={"pk": 99999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)
    
    def test_04_customer_delete_with_constraints(self):
        """Kiểm tra xóa khách hàng và ràng buộc với xe."""
        customer = create_customer("Delete Test", "0905555555")
        delete_url = reverse("customers:customer_delete", kwargs={"pk": customer.pk})
        
        # Kiểm tra xóa thành công khi không có xe
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Customer.objects.filter(pk=customer.pk).exists())
        
        # Kiểm tra bị chặn xóa khi khách hàng có xe
        customer_with_vehicle = create_customer("Has Vehicle", "0906666666")
        delete_url_2 = reverse("customers:customer_delete", kwargs={"pk": customer_with_vehicle.pk})
        
        from vehicles.models import Vehicle
        Vehicle.objects.create(plate_number="30A-99999", vehicle_type="motorcycle", customer=customer_with_vehicle)
        
        response = self.client.post(delete_url_2)
        self.assertEqual(response.status_code, 302)  # redirect với lỗi
        self.assertTrue(Customer.objects.filter(pk=customer_with_vehicle.pk).exists())  # vẫn tồn tại


class CustomerListAndDetailTests(TestCase):
    """Kiểm tra danh sách và chi tiết khách hàng."""
    
    def setUp(self):
        self.client = Client()
        self.staff = create_staff()
        self.client.force_login(self.staff)
        create_customer("Alpha Customer", "0900000001", "Khách vãng lai")
        create_customer("Beta Customer", "0900000002", "Khách gửi tháng")
    
    def test_05_customer_list_search_and_filter(self):
        """Kiểm tra danh sách, tìm kiếm và lọc khách hàng."""
        list_url = reverse("customers:customer_list")
        
        # Kiểm tra danh sách cơ bản
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        
        # Kiểm tra tìm kiếm theo tên
        response = self.client.get(list_url, {"q": "Alpha"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha Customer")
        self.assertNotContains(response, "Beta Customer")
        
        # Kiểm tra lọc theo loại khách hàng
        response = self.client.get(list_url, {"type": "monthly"})
        self.assertContains(response, "Beta Customer")
        
        response = self.client.get(list_url, {"type": "guest"})
        self.assertContains(response, "Alpha Customer")
    
    def test_06_customer_detail_view(self):
        """Kiểm tra trang chi tiết khách hàng."""
        customer = create_customer("Detail Test", "0907777777")
        detail_url = reverse("customers:customer_detail", kwargs={"pk": customer.pk})
        
        # Kiểm tra xem chi tiết thành công
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detail Test")
        
        # Kiểm tra 404 cho khách hàng không tồn tại
        invalid_url = reverse("customers:customer_detail", kwargs={"pk": 99999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)


class CustomerAccessControlTests(TestCase):
    """Kiểm tra phân quyền truy cập."""
    
    def test_07_customer_access_requires_authentication(self):
        """Kiểm tra yêu cầu đăng nhập cho tất cả customer views."""
        client = Client()
        
        # Kiểm tra tất cả endpoint chính yêu cầu đăng nhập
        urls_to_test = [
            reverse("customers:customer_list"),
            reverse("customers:customer_add"),
        ]
        
        for url in urls_to_test:
            response = client.get(url)
            self.assertEqual(response.status_code, 302)  # redirect đến login
        
        # Kiểm tra với các endpoint khách hàng cụ thể
        staff = create_staff()
        customer = create_customer()
        
        customer_urls = [
            reverse("customers:customer_edit", kwargs={"pk": customer.pk}),
            reverse("customers:customer_delete", kwargs={"pk": customer.pk}),
            reverse("customers:customer_detail", kwargs={"pk": customer.pk}),
        ]
        
        for url in customer_urls:
            response = client.get(url)
            self.assertEqual(response.status_code, 302)  # redirect đến login
