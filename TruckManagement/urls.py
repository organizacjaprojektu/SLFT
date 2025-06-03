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
from core.views import product_form, hub_form, product_list, generate_routes_view, logout_view
from core.views import manage_hub_lorries, add_lorry_to_hub, remove_lorry_from_hub, add_lorry

urlpatterns = [
        #path('admin/', admin.site.urls),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    # path('sample_data', views.sample_data),
    #    path('admin/', admin.site.urls),
    # path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('sample_data', views.sample_data),
    path('', views.home, name='root'),
    path('home/', views.home, name='home'),
    path("products/", product_list, name="product_list"),
    path("add_product/", product_form, name="add_product"),
    path("add_hub/", hub_form, name="add_hub"),
    path('generate_routes/', generate_routes_view, name='generate_routes'),
    path('hubs/<int:hub_id>/manage-lorries/', manage_hub_lorries, name='manage_hub_lorries'),
    path('hubs/<int:hub_id>/add-lorry/', add_lorry_to_hub, name='add_lorry_to_hub'),
    path('hubs/<int:hub_id>/remove-lorry/', remove_lorry_from_hub, name='remove_lorry_from_hub'),
    path('add-truck/', views.add_truck, name='add_truck'),
    path('trucks/', views.truck_list, name='truck_list'),
    path("hubs/", views.hub_list, name="hub_list"),
    path('update_order_status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('delete_order/<int:order_id>/', views.delete_order, name='delete_order'),
    path('drivers/', views.driver_list, name='driver_list'),
    path('add_driver/', views.add_driver, name='add_driver'),
    path('drivers/<int:driver_id>/manage-trucks/', views.manage_driver_trucks, name='manage_driver_trucks'),
    path('manage_trucks/', views.manage_trucks, name='manage_trucks'),

]
