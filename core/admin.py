from django.contrib import admin
from .models import Truck, Driver, Order, Cargo

admin.site.register(Truck)
admin.site.register(Driver)
admin.site.register(Order)
admin.site.register(Cargo)