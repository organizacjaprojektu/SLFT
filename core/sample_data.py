from datetime import datetime

from django.contrib.auth.models import User
from core.models import Truck, Hub, Driver, Cargo, Order, ProductRoute
from django.utils import timezone
import json
import uuid

def create_sample_data():
    # Clear existing data to avoid conflicts (optional, comment out if not needed)
    ProductRoute.objects.all().delete()
    Order.objects.all().delete()
    Cargo.objects.all().delete()
    Driver.objects.all().delete()
    Hub.objects.all().delete()
    Truck.objects.all().delete()
    User.objects.all().delete()

    # Create a dispatcher
    dispatcher = User.objects.create_user(
        username='dispatcher1',
        password='password123',
        first_name='Jan',
        last_name='Kowalski'
    )

    # Create Trucks
    truck1 = Truck.objects.create(
        registration_number=str(uuid.uuid4())[:20],
        brand='Volvo',
        model='FH16',
        capacity=24.0,
        is_available=True
    )
    truck2 = Truck.objects.create(
        registration_number=str(uuid.uuid4())[:20],
        brand='Scania',
        model='R450',
        capacity=20.0,
        is_available=True
    )
    truck3 = Truck.objects.create(
        registration_number=str(uuid.uuid4())[:20],
        brand='MAN',
        model='TGX',
        capacity=30.0,
        is_available=True
    )

    # Create Hubs
    hub1 = Hub.objects.create(
        name='Warszawa Hub',
        location_latitude=52.2297,
        location_longitude=21.0122
    )
    hub2 = Hub.objects.create(
        name='Kraków Hub',
        location_latitude=50.0647,
        location_longitude=19.9450
    )
    hub3 = Hub.objects.create(
        name='Gdańsk Hub',
        location_latitude=54.3520,
        location_longitude=18.6466
    )
    hub4 = Hub.objects.create(
        name='Wrocław Hub',
        location_latitude=51.1079,
        location_longitude=17.0385
    )

    # Assign Trucks to Hubs
    hub1.trucks.add(truck1, truck2)
    hub2.trucks.add(truck3)
    hub3.trucks.add(truck1)  # Truck1 available in multiple hubs for flexibility
    hub4.trucks.add(truck2)

    # Create Drivers
    driver_user1 = User.objects.create_user(
        username='driver1',
        password='password123',
        first_name='Adam',
        last_name='Nowak'
    )
    driver_user2 = User.objects.create_user(
        username='driver2',
        password='password123',
        first_name='Ewa',
        last_name='Wiśniewska'
    )
    driver_user3 = User.objects.create_user(
        username='driver3',
        password='password123',
        first_name='Piotr',
        last_name='Zieliński'
    )

    driver1 = Driver.objects.create(
        user=driver_user1,
        license_number='XYZ789',
        phone_number='+48 123 456 789',
        is_available=True
    )
    driver2 = Driver.objects.create(
        user=driver_user2,
        license_number='ABC123',
        phone_number='+48 987 654 321',
        is_available=True
    )
    driver3 = Driver.objects.create(
        user=driver_user3,
        license_number='DEF456',
        phone_number='+48 555 555 555',
        is_available=True
    )

    # Create Cargos
    cargo1 = Cargo.objects.create(
        name='Cement',
        description='Cement portlandzki, 25kg worki',
        weight=20.0,
        is_fragile=False,
        special_requirements='Store in dry conditions'
    )
    cargo2 = Cargo.objects.create(
        name='Electronics',
        description='Fragile electronic components',
        weight=5.0,
        is_fragile=True,
        special_requirements='Handle with care, avoid shocks'
    )
    cargo3 = Cargo.objects.create(
        name='Furniture',
        description='Wooden furniture sets',
        weight=15.0,
        is_fragile=False,
        special_requirements='Secure tightly to prevent movement'
    )

    # Define sample route combinations for orders
    # Order 1: Warszawa -> Kraków
    combinations1 = [
        [
            {
                "hub": {"id": hub1.id, "name": hub1.name, "location_latitude": hub1.location_latitude, "location_longitude": hub1.location_longitude},
                "arrival_time": "2025-05-01 08:00:00",
                "time_diff": "00:00:00"
            },
            {
                "hub": {"id": hub2.id, "name": hub2.name, "location_latitude": hub2.location_latitude, "location_longitude": hub2.location_longitude},
                "arrival_time": "2025-05-01 12:00:00",
                "time_diff": "04:00:00"
            }
        ]
    ]

    # Order 2: Warszawa -> Gdańsk via Wrocław
    combinations2 = [
        [
            {
                "hub": {"id": hub1.id, "name": hub1.name, "location_latitude": hub1.location_latitude, "location_longitude": hub1.location_longitude},
                "arrival_time": "2025-05-01 08:00:00",
                "time_diff": "00:00:00"
            },
            {
                "hub": {"id": hub4.id, "name": hub4.name, "location_latitude": hub4.location_latitude, "location_longitude": hub4.location_longitude},
                "arrival_time": "2025-05-01 11:00:00",
                "time_diff": "03:00:00"
            },
            {
                "hub": {"id": hub3.id, "name": hub3.name, "location_latitude": hub3.location_latitude, "location_longitude": hub3.location_longitude},
                "arrival_time": "2025-05-01 15:00:00",
                "time_diff": "07:00:00"
            }
        ]
    ]

    # Order 3: Kraków -> Gdańsk
    combinations3 = [
        [
            {
                "hub": {"id": hub2.id, "name": hub2.name, "location_latitude": hub2.location_latitude, "location_longitude": hub2.location_longitude},
                "arrival_time": "2025-05-01 09:00:00",
                "time_diff": "00:00:00"
            },
            {
                "hub": {"id": hub3.id, "name": hub3.name, "location_latitude": hub3.location_latitude, "location_longitude": hub3.location_longitude},
                "arrival_time": "2025-05-01 14:00:00",
                "time_diff": "05:00:00"
            }
        ]
    ]

    # Create Orders
    order1 = Order.objects.create(
        order_number=str(uuid.uuid4())[:20],
        description='Delivery of cement from Warszawa to Kraków',
        pickup_address='Warszawa, ul. Przemysłowa 1',
        delivery_address='Kraków, ul. Handlowa 5',
        status='Pending',
        truck=truck1,
        driver=driver1,
        dispatcher=dispatcher,
        cargo=cargo1,
        name='Cement Delivery 001',
        volume=1000,
        priority=2,  # Medium priority
        deadline=datetime(2025, 5, 2, 12, 0),
        current_hub=hub1,
        will_arrive_current_hub_at=datetime(2025, 5, 1, 8, 0),
        destination_hub=hub2,
        all_combinations=json.dumps(combinations1)
    )

    order2 = Order.objects.create(
        order_number=str(uuid.uuid4())[:20],
        description='Delivery of electronics from Warszawa to Gdańsk via Wrocław',
        pickup_address='Warszawa, ul. Przemysłowa 1',
        delivery_address='Gdańsk, ul. Portowa 10',
        status='Pending',
        truck=truck2,
        driver=driver2,
        dispatcher=dispatcher,
        cargo=cargo2,
        name='Electronics Delivery 002',
        volume=500,
        priority=3,  # High priority (faster delivery)
        deadline=datetime(2025, 5, 1, 16, 0),
        current_hub=hub1,
        will_arrive_current_hub_at=datetime(2025, 5, 1, 8, 0),
        destination_hub=hub3,
        all_combinations=json.dumps(combinations2)
    )

    order3 = Order.objects.create(
        order_number=str(uuid.uuid4())[:20],
        description='Delivery of furniture from Kraków to Gdańsk',
        pickup_address='Kraków, ul. Handlowa 5',
        delivery_address='Gdańsk, ul. Portowa 10',
        status='Pending',
        truck=truck3,
        driver=driver3,
        dispatcher=dispatcher,
        cargo=cargo3,
        name='Furniture Delivery 003',
        volume=800,
        priority=1,  # Low priority (cheaper delivery)
        deadline=datetime(2025, 5, 3, 12, 0),
        current_hub=hub2,
        will_arrive_current_hub_at=datetime(2025, 5, 1, 9, 0),
        destination_hub=hub3,
        all_combinations=json.dumps(combinations3)
    )

    # Create Product Routes
    route1 = [
        {"hub_id": hub1.id, "name": hub1.name},
        {"hub_id": hub2.id, "name": hub2.name}
    ]
    ProductRoute.objects.create(
        product=order1,
        route=json.dumps(route1)
    )

    route2 = [
        {"hub_id": hub1.id, "name": hub1.name},
        {"hub_id": hub4.id, "name": hub4.name},
        {"hub_id": hub3.id, "name": hub3.name}
    ]
    ProductRoute.objects.create(
        product=order2,
        route=json.dumps(route2)
    )

    route3 = [
        {"hub_id": hub2.id, "name": hub2.name},
        {"hub_id": hub3.id, "name": hub3.name}
    ]
    ProductRoute.objects.create(
        product=order3,
        route=json.dumps(route3)
    )

    return {"status": "Sample data created successfully"}

if __name__ == '__main__':
    create_sample_data()