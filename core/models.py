from django.db import models
from django.contrib.auth.models import User

class Truck(models.Model):
    registration_number = models.CharField(max_length=20, unique=True)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    capacity = models.DecimalField(max_digits=10, decimal_places=2)  # Pojemność w tonach
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.registration_number})"

class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.license_number})"

class Cargo(models.Model):
    name = models.CharField(max_length=100)  # Nazwa ładunku
    description = models.TextField(blank=True, null=True)  # Opis ładunku
    weight = models.DecimalField(max_digits=10, decimal_places=2)  # Waga w tonach
    is_fragile = models.BooleanField(default=False)  # Czy ładunek jest delikatny?
    special_requirements = models.TextField(blank=True, null=True)  # Specjalne wymagania

    def __str__(self):
        return f"{self.name} ({self.weight} ton)"

class Order(models.Model):
    order_number = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True, null=True)
    pickup_address = models.CharField(max_length=255)
    delivery_address = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default='Pending')  # Status zamówienia
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    truck = models.ForeignKey(Truck, on_delete=models.SET_NULL, null=True, blank=True)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    dispatcher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='dispatched_orders')
    cargo = models.ForeignKey(Cargo, on_delete=models.SET_NULL, null=True, blank=True)  # Powiązanie z ładunkiem

    def __str__(self):
        return f"Order {self.order_number} ({self.status})"