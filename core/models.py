from django.contrib.auth.models import User
from django.db import models
import json


class Truck(models.Model):
    registration_number = models.CharField(max_length=20, unique=True)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    capacity = models.DecimalField(max_digits=10, decimal_places=2)  # Pojemność w tonach
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.registration_number})"


class Hub(models.Model):
    name = models.CharField(max_length=100)
    location_latitude = models.FloatField()
    location_longitude = models.FloatField()
    trucks = models.ManyToManyField(Truck)


class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.license_number})"


class Cargo(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2)  # Waga w tonach
    is_fragile = models.BooleanField(default=False)
    special_requirements = models.TextField(blank=True, null=True)

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
    name = models.CharField(max_length=100)
    volume = models.IntegerField()
    priority = models.IntegerField()  # 3 - faster delivery, 1 - cheaper delivery
    deadline = models.DateTimeField()
    current_hub = models.ForeignKey(
        'Hub', on_delete=models.CASCADE, related_name='products_at_current_hub'
    )
    will_arrive_current_hub_at = models.DateTimeField()
    destination_hub = models.ForeignKey(
        'Hub', on_delete=models.CASCADE, related_name='products_at_destination_hub'
    )
    all_combinations = models.JSONField()

    def __str__(self):
        return self.name

    def set_combinations(self, x):
        self.foo = json.dumps(x)

    def get_combinations(self):
        return json.loads(self.all_combinations)


class ProductRoute(models.Model):
    product = models.OneToOneField('Order', on_delete=models.CASCADE)
    route = models.JSONField()

    def __str__(self):
        return f"Trasa dla produktu {self.product.name}"