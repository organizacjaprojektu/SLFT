from django.contrib.auth.models import User
from .models import Truck, Driver, Cargo, Order

def create_truck(registration_number, brand, model, capacity, is_available):
    truck = Truck.objects.create(
        registration_number = registration_number,
        brand = brand,
        model = model,
        capacity = capacity,
        is_available = is_available
    )
    return truck

def create_driver(user, license_number, phone_number, is_available):
    driver = Driver.objects.create(
        user = user,
        license_number = license_number, 
        phone_number = phone_number,
        is_available = is_available
    )
    return driver

def create_cargo(name, description, weight, is_fragile=False, special_requirements=None):
    cargo = Cargo.objects.create(
        name=name,
        description=description,
        weight=weight,
        is_fragile=is_fragile,
        special_requirements=special_requirements
    )
    return cargo

def create_order(order_number, pickup_address, delivery_address, dispatcher, 
                 description=None, status='Pending', truck=None, driver=None, cargo=None):
    order = Order.objects.create(
        order_number=order_number,
        description=description,
        pickup_address=pickup_address,
        delivery_address=delivery_address,
        status=status,
        truck=truck,
        driver=driver,
        dispatcher=dispatcher,
        cargo=cargo
    )
    return order

