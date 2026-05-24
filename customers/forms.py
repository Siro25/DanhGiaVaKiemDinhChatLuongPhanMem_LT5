from django import forms
from vehicles.models import Vehicle

class VehicleRegistrationForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = ['plate_number', 'vehicle_type', 'color']
        widgets = {
            'plate_number': forms.TextInput(attrs={'class':'form-control','placeholder':'VD: 30A-123.45'}),
            'vehicle_type': forms.Select(attrs={'class':'form-select'}),
            'color': forms.TextInput(attrs={'class':'form-control','placeholder':'VD: Đỏ / Xanh / Đen', 'type':'text'}),
        }