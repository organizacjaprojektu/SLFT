"""
URL configuration for TruckManagement project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
# from django.contrib import admin
from django.urls import path
import core.views as views
from core.views import product_form, hub_form, product_list, generate_routes_view
from core.views import manage_hub_lorries, add_lorry_to_hub, remove_lorry_from_hub, add_lorry

urlpatterns = [
        #path('admin/', admin.site.urls),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('sample_data', views.sample_data),
    #    path('admin/', admin.site.urls),
    # path('login/', views.CustomLoginView.as_view(), name='login'),
    # path('sample_data', views.sample_data),

    path('home/', views.home, name='home'),
    path("products/", product_list, name="product_list"),
    path("add_product/", product_form, name="add_product"),
    path("add_hub/", hub_form, name="add_hub"),
    path('generate_routes/', generate_routes_view, name='generate_routes'),
    path('hubs/<int:hub_id>/manage-lorries/', manage_hub_lorries, name='manage_hub_lorries'),
    path('hubs/<int:hub_id>/add-lorry/', add_lorry_to_hub, name='add_lorry_to_hub'),
    path('hubs/<int:hub_id>/remove-lorry/', remove_lorry_from_hub, name='remove_lorry_from_hub'),
    path('add_lorry/', add_lorry, name='add_lorry'),
    path('add-truck/', views.add_truck, name='add_truck'),
    path('trucks/', views.truck_list, name='truck_list'),
]
