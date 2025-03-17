
from core.models import Truck, Driver, Cargo, Order  # Poprawiony import modeli
from django.contrib.auth.models import User

def create_sample_data():
    # Tworzenie użytkownika (spedytora)
    dispatcher = User.objects.create_user(
        username='dispatcher1',
        password='password123',
        first_name='Jan',
        last_name='Kowalski'
    )

    # Tworzenie ciężarówki
    truck = Truck.objects.create(
        registration_number='ABC123',
        brand='Volvo',
        model='FH16',
        capacity=24.0
    )

    # Tworzenie kierowcy
    driver_user = User.objects.create_user(
        username='driver1',
        password='password123',
        first_name='Adam',
        last_name='Nowak'
    )
    driver = Driver.objects.create(
        user=driver_user,
        license_number='XYZ789',
        phone_number='+48 123 456 789'
    )

    # Tworzenie ładunku
    cargo = Cargo.objects.create(
        name='Cement',
        description='Cement portlandzki, 25kg worki',
        weight=20.0,
        is_fragile=False
    )

    # Tworzenie zamówienia
    order = Order.objects.create(
        order_number='ORD001',
        pickup_address='Warszawa, ul. Przemysłowa 1',
        delivery_address='Kraków, ul. Handlowa 5',
        truck=truck,
        driver=driver,
        dispatcher=dispatcher,
        cargo=cargo
    )

    print("Przykładowe dane zostały dodane!")

if __name__ == '__main__':
    create_sample_data()