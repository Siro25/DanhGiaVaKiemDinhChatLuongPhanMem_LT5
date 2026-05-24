from django import forms

class PaymentFilterForm(forms.Form):
    STATUS_CHOICES = [('','Tất cả'),('pending','Chưa thanh toán'),('paid','Đã thanh toán'),('cancelled','Hủy')]
    METHOD_CHOICES = [('','Tất cả'),('cash','Tiền mặt'),('card','Thẻ'),('momo','MOMO')]

    q = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'form-control','placeholder':'Biển số / khách'}))
    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES, widget=forms.Select(attrs={'class':'form-select'}))
    method = forms.ChoiceField(required=False, choices=METHOD_CHOICES, widget=forms.Select(attrs={'class':'form-select'}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date','class':'form-control'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date','class':'form-control'}))

class GuestCheckinForm(forms.Form):
    """Form check-in cho khách vãng lai"""
    VEHICLE_TYPE_CHOICES = [
        ('motorcycle', 'Xe máy'),
        ('car', 'Ô tô'),
        ('bicycle', 'Xe đạp'),
    ]
    
    name = forms.CharField(
        label='Tên khách hàng',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập tên khách hàng'
        })
    )
    
    phone = forms.CharField(
        label='Số điện thoại',
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nhập số điện thoại'
        })
    )
    
    plate_number = forms.CharField(
        label='Biển số xe',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: 29A-12345'
        })
    )
    
    vehicle_type = forms.ChoiceField(
        label='Loại xe',
        choices=VEHICLE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    color = forms.CharField(
        label='Màu xe',
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'VD: Đỏ, Xanh, Trắng...'
        })
    )
    
    image = forms.ImageField(
        label='Hình ảnh xe (tùy chọn)',
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )