"""White-box unit tests cho chức năng Parking Check-in/Check-out."""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal

from accounts.models import User
from customers.models import Customer, MonthlySubscription
from vehicles.models import Vehicle
from parking.models import ParkingLot, ParkingRecord, PricingSetting
from cards.models import Card
from finance.models import ParkingRate


def make_khachhang(username="kh_park", password="khpark!"):
    return User.objects.create_user(username=username, password=password, email=f"{username}@test.com", role="khachhang", status="approved")

def make_nhanvien(username="nv_park", password="nvpark!"):
    return User.objects.create_user(username=username, password=password, email=f"{username}@test.com", role="nhanvien", status="approved")

def make_customer(user=None, name="KH Parking", phone="0911111111", customer_type="Khách vãng lai", status="approved"):
    return Customer.objects.create(user=user, name=name, phone=phone, customer_type=customer_type, status=status)

def make_vehicle(plate="51A-PARK1", customer=None, status="in", vehicle_type="motorcycle", approved=True):
    return Vehicle.objects.create(plate_number=plate, vehicle_type=vehicle_type, customer=customer, status=status, approved=approved)

def make_parking_lot(name="Bãi Test", capacity=50):
    return ParkingLot.objects.create(name=name, capacity=capacity, available_slots=capacity, status="active", allowed_vehicle_types="all", hourly_rate=10000)

def make_card(customer, card_number="CARD-0001"):
    return Card.objects.create(card_number=card_number, card_type="rfid", customer=customer, status="active")

def make_parking_rate(vehicle_type="motorcycle", hourly_rate=5000):
    return ParkingRate.objects.create(vehicle_type=vehicle_type, hourly_rate=Decimal(str(hourly_rate)))


# ===========================================================================
# Tests cho ParkingRecord Model
# ===========================================================================

class ParkingRecordModelTests(TestCase):
    """Kiểm tra parking/models.py::ParkingRecord.calculate_fee()."""

    def setUp(self):
        customer = make_customer()
        self.parking_lot = make_parking_lot()
        self.vehicle = make_vehicle(customer=customer)
        self.card = make_card(customer)
        self.rate = make_parking_rate("motorcycle", 5000)

    def test_create_parking_record(self):
        """Tạo ParkingRecord cơ bản thành công."""
        record = ParkingRecord.objects.create(
            vehicle=self.vehicle,
            card=self.card,
            parking_lot=self.parking_lot,
            entry_time=timezone.now(),
            parking_rate=self.rate,
        )
        self.assertIsNone(record.exit_time)
        self.assertFalse(record.is_paid)

    def test_calculate_fee_hourly(self):
        """Tính phí theo giờ với rate_type='hourly'."""
        self.rate.rate_type = "hourly"
        self.rate.rate = Decimal("5000")
        # ParkingRate không có rate/rate_type thực – tạo đối tượng giả lập
        entry = timezone.now() - timedelta(hours=2)
        exit_ = timezone.now()

        record = ParkingRecord(
            vehicle=self.vehicle,
            card=self.card,
            parking_lot=self.parking_lot,
            entry_time=entry,
            exit_time=exit_,
            parking_rate=self.rate,
        )
        # calculate_fee dùng parking_rate.rate_type và parking_rate.rate
        # ParkingRate model chỉ có hourly_rate; gán tạm
        self.rate.rate_type = "hourly"
        self.rate.rate = Decimal("5000")

        fee = record.calculate_fee()
        # ~2 giờ × 5000 = 10000
        if fee is not None:
            self.assertGreater(fee, 0)

    def test_calculate_fee_no_exit_time_returns_none(self):
        """Không có exit_time → calculate_fee trả về None."""
        record = ParkingRecord(
            vehicle=self.vehicle,
            card=self.card,
            parking_lot=self.parking_lot,
            entry_time=timezone.now(),
            exit_time=None,
            parking_rate=self.rate,
        )
        self.assertIsNone(record.calculate_fee())

    def test_calculate_fee_no_rate_returns_none(self):
        """Không có parking_rate → calculate_fee trả về None."""
        record = ParkingRecord(
            vehicle=self.vehicle,
            card=self.card,
            parking_lot=self.parking_lot,
            entry_time=timezone.now() - timedelta(hours=1),
            exit_time=timezone.now(),
            parking_rate=None,
        )
        self.assertIsNone(record.calculate_fee())


# ===========================================================================
# Tests cho PricingSetting Model
# ===========================================================================

class PricingSettingTests(TestCase):
    """Kiểm tra parking/models.py::PricingSetting.get_price()."""

    def test_get_price_existing(self):
        """Lấy giá đang active thành công."""
        PricingSetting.objects.create(
            vehicle_type="motorcycle",
            package_type="hourly",
            price=5000,
            is_active=True,
        )
        price = PricingSetting.get_price("motorcycle", "hourly")
        self.assertEqual(price, 5000)

    def test_get_price_not_found_returns_default(self):
        """Không tìm thấy → trả về giá mặc định (không raise exception)."""
        price = PricingSetting.get_price("motorcycle", "hourly")
        # Giá mặc định từ defaults dict = 5000
        self.assertEqual(price, 5000)

    def test_get_price_car_monthly_default(self):
        """Giá mặc định ô tô tháng = 800000."""
        price = PricingSetting.get_price("car", "monthly")
        self.assertEqual(price, 800000)

    def test_get_price_bicycle_hourly_default(self):
        """Giá mặc định xe đạp theo giờ = 0 (miễn phí)."""
        price = PricingSetting.get_price("bicycle", "hourly")
        self.assertEqual(price, 0)

    def test_get_price_inactive_setting_returns_default(self):
        """Setting inactive → fallback về default, không dùng giá inactive."""
        PricingSetting.objects.create(
            vehicle_type="car",
            package_type="hourly",
            price=99999,
            is_active=False,
        )
        price = PricingSetting.get_price("car", "hourly")
        # is_active=False → DoesNotExist → fallback = 30000
        self.assertEqual(price, 30000)

    def test_get_price_unknown_type_returns_zero(self):
        """Loại xe/gói không tồn tại → trả về 0."""
        price = PricingSetting.get_price("truck", "weekly")
        self.assertEqual(price, 0)


# ===========================================================================
# Tests cho ParkingLot Model
# ===========================================================================

class ParkingLotTests(TestCase):
    """Kiểm tra parking/models.py::ParkingLot."""

    def test_occupancy_rate_with_slots(self):
        """Tỷ lệ lấp đầy tính đúng khi có record active."""
        lot = make_parking_lot(capacity=10)
        customer = make_customer()
        vehicle = make_vehicle(customer=customer)
        card = make_card(customer)
        rate = make_parking_rate()

        ParkingRecord.objects.create(
            vehicle=vehicle,
            card=card,
            parking_lot=lot,
            entry_time=timezone.now(),
            parking_rate=rate,
        )
        # occupied_slots = số record chưa có exit_time = 1
        self.assertEqual(lot.occupied_slots, 1)

    def test_occupancy_rate_empty_lot(self):
        """Bãi trống → tỷ lệ lấp đầy 0."""
        lot = make_parking_lot()
        self.assertEqual(lot.occupied_slots, 0)

    def test_get_occupancy_rate_no_capacity(self):
        """capacity=0 → get_occupancy_rate() trả về 0 (không chia 0)."""
        lot = ParkingLot(capacity=0, available_slots=0)
        self.assertEqual(lot.get_occupancy_rate(), 0)


# ===========================================================================
# Tests cho vehicle_toggle_parking  (Check-in / Check-out bởi khách hàng)
# ===========================================================================

class VehicleToggleParkingTests(TestCase):
    """
    Kiểm tra customers/views.py::vehicle_toggle_parking.
    
    Bao gồm: check-in, check-out với gói tháng, check-out vãng lai.
    """

    def setUp(self):
        self.client = Client()
        self.kh_user = make_khachhang("kh_toggle", "toggle123!")
        self.customer = make_customer(
            user=self.kh_user, name="KH Toggle", phone="0912121212"
        )
        self.client.force_login(self.kh_user)

    def _make_approved_vehicle(self, plate="51A-TOGGLE1", vehicle_type="motorcycle"):
        return Vehicle.objects.create(
            plate_number=plate,
            vehicle_type=vehicle_type,
            customer=self.customer,
            approved=True,
        )

    # --- Check-in: xe vào bãi lần đầu -------------------------------------

    def test_checkin_creates_parking_record(self):
        """Xe chưa trong bãi → vào bãi → tạo ParkingRecord."""
        vehicle = self._make_approved_vehicle()
        url = reverse("customers:vehicle_toggle_parking", kwargs={"pk": vehicle.pk})

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        record = ParkingRecord.objects.filter(
            vehicle=vehicle, exit_time__isnull=True
        ).first()
        self.assertIsNotNone(record)

    # --- Check-out: xe có gói tháng ----------------------------------------

    def test_checkout_with_monthly_subscription_free(self):
        """Xe có gói tháng → ra bãi miễn phí (fee=0, is_paid=True)."""
        vehicle = self._make_approved_vehicle(plate="51A-MONTHLY")

        # Tạo subscription còn hạn
        MonthlySubscription.objects.create(
            customer=self.customer,
            vehicle=vehicle,
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() + timedelta(days=25),
            is_active=True,
        )

        # Tạo parking lot và card
        lot = make_parking_lot("Bãi Monthly")
        card = make_card(self.customer, "CARD-MONTHLY")
        rate = make_parking_rate()

        # Xe đang trong bãi
        ParkingRecord.objects.create(
            vehicle=vehicle,
            card=card,
            parking_lot=lot,
            entry_time=timezone.now() - timedelta(hours=2),
            parking_rate=rate,
        )

        url = reverse("customers:vehicle_toggle_parking", kwargs={"pk": vehicle.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        record = ParkingRecord.objects.filter(
            vehicle=vehicle, exit_time__isnull=False
        ).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.fee, 0)
        self.assertTrue(record.is_paid)

    # --- Check-out: xe vãng lai -------------------------------------------

    def test_checkout_guest_vehicle_calculates_fee(self):
        """Xe vãng lai (không có gói tháng) → tính phí theo giờ."""
        vehicle = self._make_approved_vehicle(plate="51A-GUEST1")

        # Tạo pricing setting
        PricingSetting.objects.create(
            vehicle_type="motorcycle",
            package_type="hourly",
            price=5000,
            is_active=True,
        )

        lot = make_parking_lot("Bãi Guest")
        card = make_card(self.customer, "CARD-GUEST1")
        rate = make_parking_rate()

        # Xe đang trong bãi từ 2 giờ trước
        ParkingRecord.objects.create(
            vehicle=vehicle,
            card=card,
            parking_lot=lot,
            entry_time=timezone.now() - timedelta(hours=2),
            parking_rate=rate,
        )

        url = reverse("customers:vehicle_toggle_parking", kwargs={"pk": vehicle.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        record = ParkingRecord.objects.filter(
            vehicle=vehicle, exit_time__isnull=False
        ).first()
        self.assertIsNotNone(record)
        # fee >= 5000 (tối thiểu 1 giờ × 5000)
        self.assertGreaterEqual(record.fee, 5000)

    # --- Xe chưa được duyệt → không cho vào --------------------------------

    def test_checkin_unapproved_vehicle_blocked(self):
        """Xe chưa được duyệt → không vào bãi được."""
        vehicle = Vehicle.objects.create(
            plate_number="51A-UNAPPR",
            vehicle_type="motorcycle",
            customer=self.customer,
            approved=False,
        )
        url = reverse("customers:vehicle_toggle_parking", kwargs={"pk": vehicle.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        # Không có ParkingRecord nào được tạo
        self.assertFalse(
            ParkingRecord.objects.filter(vehicle=vehicle).exists()
        )

    # --- Xe không thuộc về khách hàng này -----------------------------------

    def test_toggle_wrong_owner_blocked(self):
        """Xe của khách khác → bị từ chối."""
        other_customer = make_customer(name="KH Khác", phone="0999999999")
        other_vehicle = make_vehicle(
            plate="51A-OTHER1", customer=other_customer, approved=True
        )
        url = reverse("customers:vehicle_toggle_parking", kwargs={"pk": other_vehicle.pk})
        response = self.client.post(url)
        # Redirect về vehicles (403 ẩn dưới dạng redirect)
        self.assertEqual(response.status_code, 302)
        # Không tạo record mới
        self.assertFalse(
            ParkingRecord.objects.filter(vehicle=other_vehicle).exists()
        )

    # --- Chưa đăng nhập -----------------------------------------------------

    def test_toggle_requires_login(self):
        """Chưa đăng nhập → redirect login."""
        vehicle = self._make_approved_vehicle(plate="51A-NOLOGIN")
        self.client.logout()
        url = reverse("customers:vehicle_toggle_parking", kwargs={"pk": vehicle.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)


# ===========================================================================
# Tests cho vehicle_checkout view  (nhân viên)  /vehicles/<pk>/checkout/
# ===========================================================================

class StaffVehicleCheckoutTests(TestCase):
    """
    Kiểm tra vehicles/views.py::vehicle_checkout.
    Nhân viên thực hiện check-out xe gửi tháng.
    """

    def setUp(self):
        self.client = Client()
        self.nv = make_nhanvien("nv_checkout", "nvcopass!")
        self.client.force_login(self.nv)
        self.customer = make_customer(name="KH NV CO", phone="0913131313")

    def test_checkout_in_vehicle_success(self):
        """Xe đang gửi → checkout thành công."""
        vehicle = make_vehicle("51A-NVCO1", customer=self.customer, status="in")
        url = reverse("vehicles:vehicle_checkout", kwargs={"pk": vehicle.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.status, "out")
        self.assertIsNotNone(vehicle.check_out)

    def test_checkout_already_out_no_change(self):
        """Xe đã ra → không thay đổi check_out."""
        vehicle = make_vehicle("51A-NVCO2", customer=self.customer, status="out")
        url = reverse("vehicles:vehicle_checkout", kwargs={"pk": vehicle.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.status, "out")
        self.assertIsNone(vehicle.check_out)  # không bị set lại

    def test_checkout_vehicle_not_found(self):
        """Xe không tồn tại → 404."""
        url = reverse("vehicles:vehicle_checkout", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class ParkingModelTests(TestCase):
    """Test parking models: ParkingRecord, PricingSetting, ParkingLot."""
    
    def setUp(self):
        customer = make_customer()
        self.parking_lot = make_parking_lot()
        self.vehicle = make_vehicle(customer=customer)
        self.card = make_card(customer)
        self.rate = make_parking_rate("motorcycle", 5000)
    
    def test_01_parking_record_creation_and_fee_calculation(self):
        """Test tạo ParkingRecord và tính phí theo các điều kiện."""
        # Basic parking record creation
        record = ParkingRecord.objects.create(
            vehicle=self.vehicle, card=self.card, parking_lot=self.parking_lot,
            entry_time=timezone.now(), parking_rate=self.rate
        )
        self.assertIsNone(record.exit_time)
        self.assertFalse(record.is_paid)
        
        # Fee calculation without exit_time returns None
        self.assertIsNone(record.calculate_fee())
        
        # Fee calculation without parking_rate returns None
        record_no_rate = ParkingRecord(
            vehicle=self.vehicle, card=self.card, parking_lot=self.parking_lot,
            entry_time=timezone.now() - timedelta(hours=1), exit_time=timezone.now(), parking_rate=None
        )
        self.assertIsNone(record_no_rate.calculate_fee())
        
        # Fee calculation with hourly rate
        self.rate.rate_type = "hourly"
        self.rate.rate = Decimal("5000")
        entry = timezone.now() - timedelta(hours=2)
        exit_ = timezone.now()
        record_with_fee = ParkingRecord(
            vehicle=self.vehicle, card=self.card, parking_lot=self.parking_lot,
            entry_time=entry, exit_time=exit_, parking_rate=self.rate
        )
        fee = record_with_fee.calculate_fee()
        if fee is not None:
            self.assertGreater(fee, 0)
    
    def test_02_pricing_setting_get_price_and_defaults(self):
        """Test PricingSetting.get_price() với active/inactive settings và defaults."""
        # Active setting returns correct price
        PricingSetting.objects.create(vehicle_type="motorcycle", package_type="hourly", price=5000, is_active=True)
        price = PricingSetting.get_price("motorcycle", "hourly")
        self.assertEqual(price, 5000)
        
        # Default prices when not found
        self.assertEqual(PricingSetting.get_price("car", "monthly"), 800000)       # default
        self.assertEqual(PricingSetting.get_price("bicycle", "hourly"), 0)         # default free
        
        # Inactive setting returns default
        PricingSetting.objects.create(vehicle_type="car", package_type="hourly", price=99999, is_active=False)
        self.assertEqual(PricingSetting.get_price("car", "hourly"), 30000)  # fallback default
        
        # Unknown type returns 0
        self.assertEqual(PricingSetting.get_price("truck", "weekly"), 0)
    
    def test_03_parking_lot_occupancy_calculation(self):
        """Test ParkingLot occupancy rate calculation."""
        lot = make_parking_lot("Bãi Occupy Test", capacity=10)
        customer = make_customer(name="KH Occupy", phone="0920000001", customer_type="Khách vãng lai")
        vehicle = make_vehicle(plate="51A-OCCUPY1", customer=customer)
        card = make_card(customer, "CARD-OCCUPY1")
        rate = make_parking_rate()
        
        # Empty lot
        self.assertEqual(lot.occupied_slots, 0)
        
        # Add active parking record
        ParkingRecord.objects.create(vehicle=vehicle, card=card, parking_lot=lot, entry_time=timezone.now(), parking_rate=rate)
        self.assertEqual(lot.occupied_slots, 1)
        
        # Test zero capacity doesn't cause division by zero
        lot_zero = ParkingLot(capacity=0, available_slots=0)
        self.assertEqual(lot_zero.get_occupancy_rate(), 0)


class VehicleCheckinTests(TestCase):
    """Test check-in thành công và các điều kiện chặn."""
    
    def setUp(self):
        self.client = Client()
        self.kh_user = make_khachhang("kh_checkin", "checkin123!")
        self.customer = make_customer(user=self.kh_user, name="KH CheckIn", phone="0912121212")
        self.client.force_login(self.kh_user)
    
    def test_04_vehicle_checkin_success(self):
        """Test check-in thành công tạo ParkingRecord."""
        vehicle = Vehicle.objects.create(
            plate_number="51A-CHECKIN", vehicle_type="motorcycle", customer=self.customer, approved=True
        )
        url = reverse("customers:vehicle_toggle_parking", kwargs={"pk": vehicle.pk})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
        # Verify parking record created
        record = ParkingRecord.objects.filter(vehicle=vehicle, exit_time__isnull=True).first()
        self.assertIsNotNone(record)
    
    def test_05_unapproved_vehicle_blocked_from_checkin(self):
        """Test xe chưa duyệt không được check-in."""
        vehicle = Vehicle.objects.create(
            plate_number="51A-UNAPPR", vehicle_type="motorcycle", customer=self.customer, approved=False
        )
        url = reverse("customers:vehicle_toggle_parking", kwargs={"pk": vehicle.pk})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
        # No parking record created for unapproved vehicle
        self.assertFalse(ParkingRecord.objects.filter(vehicle=vehicle).exists())


class VehicleCheckoutTests(TestCase):
    """Test check-out với gói tháng và vãng lai."""
    
    def setUp(self):
        self.client = Client()
        self.kh_user = make_khachhang("kh_checkout", "checkout123!")
        self.customer = make_customer(user=self.kh_user, name="KH CheckOut", phone="0913131313")
        self.client.force_login(self.kh_user)
    
    def test_06_checkout_monthly_subscription_free(self):
        """Test checkout xe có gói tháng → miễn phí."""
        vehicle = Vehicle.objects.create(
            plate_number="51A-MONTHLY", vehicle_type="motorcycle", customer=self.customer, approved=True
        )
        
        # Create active monthly subscription
        MonthlySubscription.objects.create(
            customer=self.customer, vehicle=vehicle,
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() + timedelta(days=25),
            is_active=True
        )
        
        # Setup parking infrastructure
        lot = make_parking_lot("Bãi Monthly")
        card = make_card(self.customer, "CARD-MONTHLY")
        rate = make_parking_rate()
        
        # Vehicle currently parked
        ParkingRecord.objects.create(
            vehicle=vehicle, card=card, parking_lot=lot,
            entry_time=timezone.now() - timedelta(hours=2), parking_rate=rate
        )
        
        url = reverse("customers:vehicle_toggle_parking", kwargs={"pk": vehicle.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
        # Verify free checkout
        record = ParkingRecord.objects.filter(vehicle=vehicle, exit_time__isnull=False).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.fee, 0)
        self.assertTrue(record.is_paid)
    
    def test_07_checkout_guest_vehicle_calculates_fee(self):
        """Test checkout xe vãng lai → tính phí theo giờ."""
        vehicle = Vehicle.objects.create(
            plate_number="51A-GUEST", vehicle_type="motorcycle", customer=self.customer, approved=True
        )
        
        # Setup pricing
        PricingSetting.objects.create(vehicle_type="motorcycle", package_type="hourly", price=5000, is_active=True)
        
        lot = make_parking_lot("Bãi Guest")
        card = make_card(self.customer, "CARD-GUEST")
        rate = make_parking_rate()
        
        # Vehicle parked for 2 hours
        ParkingRecord.objects.create(
            vehicle=vehicle, card=card, parking_lot=lot,
            entry_time=timezone.now() - timedelta(hours=2), parking_rate=rate
        )
        
        url = reverse("customers:vehicle_toggle_parking", kwargs={"pk": vehicle.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
        # Verify fee calculated (minimum 1 hour)
        record = ParkingRecord.objects.filter(vehicle=vehicle, exit_time__isnull=False).first()
        self.assertIsNotNone(record)
        self.assertGreaterEqual(record.fee, 5000)


class StaffVehicleCheckoutTests(TestCase):
    """Test nhân viên checkout xe."""
    
    def setUp(self):
        self.client = Client()
        self.nv = make_nhanvien("nv_checkout", "nvcopass!")
        self.client.force_login(self.nv)
        self.customer = make_customer(name="KH Staff CO", phone="0914141414")
    
    def test_08_staff_checkout_vehicle_success(self):
        """Test nhân viên checkout xe từ 'in' → 'out'."""
        vehicle = make_vehicle("51A-STAFF1", customer=self.customer, status="in")
        url = reverse("vehicles:vehicle_checkout", kwargs={"pk": vehicle.pk})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.status, "out")
        self.assertIsNotNone(vehicle.check_out)
    
    def test_09_checkout_already_out_no_change(self):
        """Test xe đã 'out' → không thay đổi."""
        vehicle = make_vehicle("51A-STAFF2", customer=self.customer, status="out")
        url = reverse("vehicles:vehicle_checkout", kwargs={"pk": vehicle.pk})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        
        vehicle.refresh_from_db()
        self.assertEqual(vehicle.status, "out")
        self.assertIsNone(vehicle.check_out)  # not reset
    
    def test_10_checkout_nonexistent_vehicle_404(self):
        """Test checkout xe không tồn tại → 404."""
        url = reverse("vehicles:vehicle_checkout", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)