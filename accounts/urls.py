from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('user_login/', views.user_login_view, name='user_login'),
    path('admin_login/', views.admin_login_view, name='admin_login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard-nhanvien/', views.nhanvien_dashboard, name='dashboard-nhanvien'),
    path('dashboard-khachhang/', views.dashboard, name='dashboard-khachhang'),
    path('dashboard_admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/nhanvien/', views.nhanvien_dashboard, name='dashboard-nhanvien'),
    path('settings/nhanvien/', views.nhanvien_settings, name='nhanvien_settings'),
    path('users/', views.UserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/add/', views.UserCreateView.as_view(), name='user-create'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user-update'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user-delete'),
    # Quản lý nhân viên
    path('admin/employees/', views.employee_management, name='employee_management'),
    path('admin/employees/<int:employee_id>/approve/', views.approve_employee, name='approve_employee'),
    path('admin/employees/<int:employee_id>/reject/', views.reject_employee, name='reject_employee'),
    # CRUD nhân viên
    path('admin/employees/create/', views.employee_create, name='employee_create'),
    path('admin/employees/<int:employee_id>/detail/', views.employee_detail, name='employee_detail'),
    path('admin/employees/<int:employee_id>/update/', views.employee_update, name='employee_update'),
    path('admin/employees/<int:employee_id>/delete/', views.employee_delete, name='employee_delete'),
    # Báo cáo thống kê
    path('admin/reports/', views.reports_dashboard, name='reports_dashboard'),
    # Quản lý admin nâng cao
    path('admin/customers/', views.admin_customer_management, name='admin_customer_management'),
    path('admin/customers/export/', views.export_customers_excel, name='export_customers_excel'),
    path('admin/payments/', views.admin_payment_management, name='admin_payment_management'),
    path('admin/payments/export/', views.export_payments_excel, name='export_payments_excel'),
    
    # Data cleaning functions
    path('admin/payments/clean-old-data/', views.clean_old_data, name='clean_old_data'),
    path('admin/payments/clean-cancelled-transactions/', views.clean_cancelled_transactions, name='clean_cancelled_transactions'),
    path('admin/payments/clean-duplicate-transactions/', views.clean_duplicate_transactions, name='clean_duplicate_transactions'),
    path('admin/payments/delete-transaction/<int:transaction_id>/', views.delete_specific_transaction, name='delete_specific_transaction'),
    
    # Transaction approval
    path('admin/transactions/<int:transaction_id>/approve/', views.approve_transaction, name='approve_transaction'),
    path('admin/transactions/<int:transaction_id>/reject/', views.reject_transaction, name='reject_transaction'),
    
    # System settings
    path('admin/settings/', views.system_settings, name='system_settings'),
    path('admin/salary-api/', views.salary_management_api, name='salary_management_api'),
]