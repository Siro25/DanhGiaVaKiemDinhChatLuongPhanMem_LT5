from django.urls import path
from . import views

app_name = 'cards'

urlpatterns = [
    path('', views.payment_list, name='payment_list'),   # /cards/ -> list
    path('create_from_vehicle/<int:vehicle_pk>/', views.create_from_vehicle, name='create_from_vehicle'),
    path('<int:pk>/', views.payment_detail, name='payment_detail'),
    path('<int:pk>/pay/', views.mark_paid, name='mark_paid'),
    path('payments/<int:pk>/cancel/', views.cancel_payment, name='cancel_payment'),
    path('payments/export/', views.export_payments_csv, name='export_payments_csv'),
    # Quản lý khách vãng lai
    path('guest-customers/', views.guest_customer_list, name='guest_customer_list'),
    path('guest-customers/checkin/', views.guest_checkin, name='guest_checkin'),
    path('guest-customers/<int:customer_id>/vehicles/', views.guest_customer_vehicles, name='guest_customer_vehicles'),
]
custom_tags = {
    'export_payments_csv': 'cards.export_payments_csv',
}