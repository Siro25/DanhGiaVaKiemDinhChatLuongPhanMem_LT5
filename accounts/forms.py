from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
# Form để tạo và cập nhật nhân viên
class EmployeeForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Mật khẩu',
        required=False
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Xác nhận mật khẩu',
        required=False
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'phone_number', 'status']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Tên đăng nhập',
            'email': 'Email',
            'full_name': 'Họ và tên',
            'phone_number': 'Số điện thoại',
            'status': 'Trạng thái',
        }
    
    def __init__(self, *args, **kwargs):
        self.is_update = kwargs.pop('is_update', False)
        super().__init__(*args, **kwargs)
        
        if self.is_update:
            # Khi cập nhật, mật khẩu không bắt buộc
            self.fields['password'].help_text = 'Để trống nếu không muốn thay đổi mật khẩu'
            self.fields['confirm_password'].help_text = 'Để trống nếu không muốn thay đổi mật khẩu'
        else:
            # Khi tạo mới, mật khẩu bắt buộc
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if not self.is_update or password:
            if password != confirm_password:
                raise forms.ValidationError('Mật khẩu xác nhận không khớp')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'nhanvien'  # Đặt vai trò là nhân viên
        
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
        return user

class EmployeeCreateForm(EmployeeForm):
    def __init__(self, *args, **kwargs):
        kwargs['is_update'] = False
        super().__init__(*args, **kwargs)

class EmployeeUpdateForm(EmployeeForm):
    def __init__(self, *args, **kwargs):
        kwargs['is_update'] = True
        super().__init__(*args, **kwargs)


# Simple login form used by `login_view` and `user_login_view`.
class LoginForm(forms.Form):
    identifier = forms.CharField(
        label='Email hoặc tên đăng nhập',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email hoặc username'})
    )
    password = forms.CharField(
        label='Mật khẩu',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mật khẩu'})
    )

    def clean_identifier(self):
        ident = self.cleaned_data.get('identifier')
        if not ident:
            raise forms.ValidationError('Vui lòng nhập email hoặc tên đăng nhập')
        return ident