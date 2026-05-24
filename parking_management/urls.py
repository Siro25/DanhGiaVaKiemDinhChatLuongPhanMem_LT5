"""
URL configuration for parking_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('customers/', include(('customers.urls', 'customers'), namespace='customers')),
    path('cards/', include(('cards.urls', 'cards'), namespace='cards')),
    path('payments/', RedirectView.as_view(url='/cards/', permanent=False)),  # alias to cards
    path('parking/', include(('parking.urls', 'parking'), namespace='parking')),
    path('', RedirectView.as_view(url='accounts/login/', permanent=True)),
    path('vehicles/', include('vehicles.urls')),
    path('pricing/', include('pricing.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
