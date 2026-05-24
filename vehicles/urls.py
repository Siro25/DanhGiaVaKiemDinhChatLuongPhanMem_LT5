from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    path('', views.vehicle_list, name='vehicle_list'),
    path('add/', views.vehicle_add, name='vehicle_add'),
    path('<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('<int:pk>/edit/', views.vehicle_edit, name='vehicle_edit'),
    path('<int:pk>/checkout/', views.vehicle_checkout, name='vehicle_checkout'),
    path('<int:pk>/delete/', views.vehicle_delete, name='vehicle_delete'),
    path('export/', views.export_vehicles_excel, name='export_vehicles_excel'),
]