from django.urls import path
from . import views
from . import subscription_views
from . import wallet_views

app_name = 'customers'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('vehicles/', views.vehicles_list, name='vehicles'),
    path('vehicles/pending/', views.pending_vehicles, name='pending_vehicles'),
    path('vehicles/register/', views.vehicle_register, name='vehicle_register'),
    path('vehicles/<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('vehicles/<int:pk>/approve/', views.vehicle_approve, name='vehicle_approve'),
    path('vehicles/<int:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),
    path('vehicles/<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),
    path('vehicles/<int:pk>/toggle-parking/', views.vehicle_toggle_parking, name='vehicle_toggle_parking'),
    path('payment/<int:pk>/', views.payment, name='payment'),
    path('payments/', views.payment_history, name='payment_history'),
    path('subscribe/', subscription_views.subscribe_monthly, name='subscribe_monthly'),
    path('wallet/', wallet_views.wallet_view, name='wallet'),
    path('wallet/deposit/', wallet_views.wallet_deposit, name='wallet_deposit'),
    path('wallet/pay-debt/<int:record_id>/', wallet_views.pay_debt, name='pay_debt'),
    path('wallet/pay-all-debt/', wallet_views.pay_all_debt, name='pay_all_debt'),
    path('history/', views.history, name='history'),
    path('support/', views.support, name='support'),

    # existing admin/customer management routes
    path('list/', views.customer_list, name='customer_list'),
    path('add/', views.customer_add, name='customer_add'),
    path('detail/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('edit/<int:pk>/', views.customer_edit, name='customer_edit'),
    path('delete/<int:pk>/', views.customer_delete, name='customer_delete'),
]