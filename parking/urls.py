from django.urls import path
from . import views

app_name = 'parking'

urlpatterns = [
    path('', views.parking_dashboard, name='dashboard'),
    path('pricing/', views.pricing_list, name='pricing_list'),
    path('admin/pricing/', views.admin_pricing_settings, name='admin_pricing_settings'),
]
