"""White-box unit tests cho chức năng quản lý phương tiện (Vehicle Management)."""

import uuid
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from customers.models import Customer
from vehicles.models import Vehicle
from vehicles.forms import VehicleForm


def make_nhanvien(username="nv_vehicle", password="nvpass!"):
    return User.objects.create_user(username=username, password=password, email=f"{username}@test.com", role="nhanvien", status="approved")

def make_customer(name="Khách VL", phone="0900000001", customer_type="Khách vãng lai"):
    return Customer.objects.create(name=name, phone=phone, customer_type=customer_type)

def make_vehicle(plate="30A-00001", customer=None, status="in", vehicle_type="motorcycle"):
    return Vehicle.objects.create(plate_number=plate, vehicle_type=vehicle_type, color="Đỏ", customer=customer, status=status)


class VehicleModelTests(TestCase):
    """Test Vehicle model: creation, validation, unique constraints."""
    
    def setUp(self):
        self.customer = make_customer()
    
    def test_01_vehicle_model_creation_and_validation(self):
        """Test tạo vehicle, __str__, unique plate constraint."""
        # Basic creation
        vehicle = make_vehicle(customer=self.customer)
        self.assertEqual(vehicle.plate_number, "30A-00001")
        self.assertEqual(vehicle.vehicle_type, "motorcycle")
        self.assertEqual(vehicle.status, "in")  # default
        
        # __str__ representation
        vehicle_car = make_vehicle(plate="51A-11111", customer=self.customer, vehicle_type="car")
        str_repr = str(vehicle_car)
        self.assertIn("51A-11111", str_repr)
        self.assertIn("Ô tô", str_repr)
        
    def test_01b_vehicle_unique_constraint(self):
        """Test unique plate number constraint riêng biệt."""
        # Tạo vehicle đầu tiên
        make_vehicle(plate="UNIQUE-TEST1", customer=self.customer)
        
        # Unique plate number constraint
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            make_vehicle(plate="UNIQUE-TEST1")  # duplicate plate
        
    def test_01c_vehicle_type_choices_validation(self):
        """Test vehicle type choices validation riêng biệt."""
        # Vehicle type choices validation
        valid_types = [t[0] for t in Vehicle.VEHICLE_TYPE_CHOICES]
        for i, vt in enumerate(valid_types):
            unique_plate = f"VT-{i:02d}-{str(uuid.uuid4())[:6]}"  # Đảm bảo unique
            vehicle = Vehicle.objects.create(
                plate_number=unique_plate, vehicle_type=vt, customer=self.customer
            )
            self.assertEqual(vehicle.vehicle_type, vt)
        
        # Vehicle without customer allowed
        vehicle_no_customer = Vehicle.objects.create(
            plate_number=f"NO-CUST-{str(uuid.uuid4())[:6]}", 
            vehicle_type="bicycle"
        )
        self.assertIsNone(vehicle_no_customer.customer)
    
    def test_02_vehicle_status_update_and_checkout(self):
        """Test update status và checkout timestamp."""
        from django.utils import timezone
        vehicle = make_vehicle()
        
        # Update status to 'out' with checkout time
        vehicle.check_out = timezone.now()
        vehicle.status = "out"
        vehicle.save()
        
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.status, "out")
        self.assertIsNotNone(vehicle.check_out)


class VehicleFormTests(TestCase):
    """Test VehicleForm validation."""
    
    def setUp(self):
        self.customer = Customer.objects.create(name="KH Gửi Tháng", phone="0901111111", customer_type="Khách gửi tháng")
    
    def test_03_vehicle_form_validation(self):
        """Test form validation: valid data và missing required fields."""
        from parking.models import ParkingLot
        ParkingLot.objects.create(name="Bãi A", capacity=10, available_slots=10, status="active", allowed_vehicle_types="all")
        
        # Valid form
        data = {
            "plate_number": "51A-VALID1", "vehicle_type": "motorcycle", "color": "Xanh",
            "customer": self.customer.pk, "parking_lot": ""
        }
        form = VehicleForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        
        # Missing plate number
        data_invalid = {
            "plate_number": "", "vehicle_type": "motorcycle", "color": "", "customer": self.customer.pk
        }
        form_invalid = VehicleForm(data=data_invalid)
        self.assertFalse(form_invalid.is_valid())
        self.assertIn("plate_number", form_invalid.errors)


class VehicleCRUDViewTests(TestCase):
    """Test CRUD operations: add, edit, delete vehicles."""
    
    def setUp(self):
        self.client = Client()
        self.nv = make_nhanvien()
        self.client.force_login(self.nv)
        self.customer = make_customer(name="KH CRUD", customer_type="Khách gửi tháng")
    
    def test_04_vehicle_add_success_and_duplicate_plate(self):
        """Test thêm vehicle thành công và xử lý biển số trùng."""
        add_url = reverse("vehicles:vehicle_add")
        
        # Successful add
        data = {
            "plate_number": "51A-ADD01", "vehicle_type": "motorcycle", "color": "Đen",
            "customer": self.customer.pk, "parking_lot": ""
        }
        response = self.client.post(add_url, data)
        self.assertEqual(response.status_code, 302)  # redirect on success
        self.assertTrue(Vehicle.objects.filter(plate_number="51A-ADD01").exists())
        
        # Duplicate plate number
        data_dup = {
            "plate_number": "51A-ADD01", "vehicle_type": "car", "color": "Trắng",
            "customer": "", "parking_lot": ""
        }
        response = self.client.post(add_url, data_dup)
        self.assertEqual(response.status_code, 200)  # stays on form
        self.assertEqual(Vehicle.objects.filter(plate_number="51A-ADD01").count(), 1)  # only one exists
        
        # Missing plate number
        data_missing = {"plate_number": "", "vehicle_type": "motorcycle", "color": "", "customer": "", "parking_lot": ""}
        response = self.client.post(add_url, data_missing)
        self.assertEqual(response.status_code, 200)  # stays on form
    
    def test_05_vehicle_edit_and_validation(self):
        """Test edit vehicle và validation."""
        vehicle = make_vehicle("30A-EDIT1", customer=self.customer)
        edit_url = reverse("vehicles:vehicle_edit", kwargs={"pk": vehicle.pk})
        
        # Successful edit
        data = {
            "plate_number": "30A-EDIT1", "vehicle_type": "motorcycle", "color": "Vàng",
            "customer": self.customer.pk, "parking_lot": ""
        }
        response = self.client.post(edit_url, data)
        self.assertEqual(response.status_code, 302)
        
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.color, "Vàng")
        
        # Invalid edit: empty plate
        data_invalid = {
            "plate_number": "", "vehicle_type": "motorcycle", "color": "Vàng",
            "customer": self.customer.pk, "parking_lot": ""
        }
        response = self.client.post(edit_url, data_invalid)
        self.assertEqual(response.status_code, 200)  # stays on form
        
        # Edit nonexistent vehicle
        invalid_url = reverse("vehicles:vehicle_edit", kwargs={"pk": 99999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)
    
    def test_06_vehicle_checkout_by_staff(self):
        """Test nhân viên checkout vehicle."""
        vehicle = make_vehicle("51A-CHKOUT", customer=self.customer, status="in")
        checkout_url = reverse("vehicles:vehicle_checkout", kwargs={"pk": vehicle.pk})
        
        # Checkout vehicle currently 'in'
        response = self.client.get(checkout_url)
        self.assertEqual(response.status_code, 302)
        
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.status, "out")
        self.assertIsNotNone(vehicle.check_out)
        
        # Checkout already 'out' vehicle
        from django.utils import timezone
        vehicle_out = make_vehicle("51A-OUT", customer=self.customer, status="out")
        vehicle_out.check_out = timezone.now()
        vehicle_out.save()
        old_checkout = vehicle_out.check_out
        
        checkout_url_2 = reverse("vehicles:vehicle_checkout", kwargs={"pk": vehicle_out.pk})
        response = self.client.get(checkout_url_2)
        self.assertEqual(response.status_code, 302)
        
        vehicle_out.refresh_from_db()
        self.assertEqual(vehicle_out.status, "out")  # still out
        
        # Checkout nonexistent vehicle
        invalid_url = reverse("vehicles:vehicle_checkout", kwargs={"pk": 99999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)
    
    def test_07_vehicle_delete(self):
        """Test delete vehicle."""
        vehicle = make_vehicle("30A-DEL01", customer=self.customer)
        delete_url = reverse("vehicles:vehicle_delete", kwargs={"pk": vehicle.pk})
        
        # Successful delete
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Vehicle.objects.filter(pk=vehicle.pk).exists())
        
        # Delete nonexistent vehicle
        invalid_url = reverse("vehicles:vehicle_delete", kwargs={"pk": 99999})
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 404)


class VehicleListAndFilterTests(TestCase):
    """Test vehicle list, search, và filter."""
    
    def setUp(self):
        self.client = Client()
        self.nv = make_nhanvien("nv_list", "listpass!")
        self.client.force_login(self.nv)
        
        c_monthly = make_customer("KH Tháng", "0905555550", "Khách gửi tháng")
        c_guest = make_customer("KH Lai", "0905555551", "Khách vãng lai")
        make_vehicle("30A-LIST01", customer=c_monthly)
        make_vehicle("30A-LIST02", customer=c_guest)
    
    def test_08_vehicle_list_filter_and_search(self):
        """Test list vehicle với filter và search."""
        list_url = reverse("vehicles:vehicle_list")
        
        # Default list (monthly customers)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        
        # Filter by customer type
        response = self.client.get(list_url, {"customer_type": "guest"})
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(list_url, {"customer_type": "all"})
        self.assertEqual(response.status_code, 200)
        
        # Search by plate number
        response = self.client.get(list_url, {"q": "LIST01", "customer_type": "all"})
        self.assertEqual(response.status_code, 200)
        
        # Access without login (no @login_required in current implementation)
        self.client.logout()
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
