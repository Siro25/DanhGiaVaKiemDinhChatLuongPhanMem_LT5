from django import forms
from .models import Vehicle
from customers.models import Customer
from parking.models import ParkingLot

STATUS_CHOICES = [
    ('', 'Tất cả'),
    ('in', 'Đang gửi'),
    ('out', 'Ra'),
    ('available', 'Sẵn sàng'),
]

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        # Thêm parking_lot vào form
        fields = ['plate_number', 'vehicle_type', 'color', 'customer', 'parking_lot', 'image']
        widgets = {
            'vehicle_type': forms.Select(attrs={'class': 'form-select'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'parking_lot': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Chỉ hiển thị khách gửi tháng trong dropdown
        self.fields['customer'].queryset = Customer.objects.filter(
            customer_type='Khách gửi tháng'
        ).order_by('name')
        self.fields['customer'].empty_label = "-- Chọn khách hàng gửi tháng --"
        
        # Lọc bãi xe dựa trên loại phương tiện
        if self.instance and self.instance.vehicle_type:
            vehicle_type = self.instance.vehicle_type
            # Xe nhỏ: motorcycle, bicycle
            if vehicle_type in ['motorcycle', 'bicycle']:
                allowed_types = ['small', 'all']
            # Xe to: car, truck, taxi
            else:
                allowed_types = ['large', 'all']
            
            self.fields['parking_lot'].queryset = ParkingLot.objects.filter(
                status='active',
                allowed_vehicle_types__in=allowed_types
            ).order_by('name')
        else:
            # Nếu chưa có loại xe, hiển thị tất cả bãi active
            self.fields['parking_lot'].queryset = ParkingLot.objects.filter(status='active').order_by('name')
        
        self.fields['parking_lot'].empty_label = "-- Chọn bãi xe --"
        self.fields['parking_lot'].required = False

class VehicleFilterForm(forms.Form):
    q = forms.CharField(required=False, label='', widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Tìm biển số / chủ'
    }))
    vehicle_type = forms.ChoiceField(required=False, choices=[
        ('', 'Tất cả loại xe'),
        ('motorcycle', 'Xe máy'),
        ('car', 'Ô tô'),
        ('bicycle', 'Xe đạp'),
    ], widget=forms.Select(attrs={'class':'form-select'}))
    owner = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control', 'placeholder':'Chủ / tên'}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date','class':'form-control', 'placeholder': 'Từ ngày'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date','class':'form-control', 'placeholder': 'Đến ngày'}))