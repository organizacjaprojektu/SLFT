from datetime import datetime

from django.contrib.auth.models import User
from core.models import Truck, Hub, Driver, Cargo, Order, ProductRoute
from django.utils import timezone
import json
import uuid

def create_sample_data():

    # Create a dispatcher
    User.objects.create_user(
        username='dispatcher1',
        password='password123',
        first_name='Jan',
        last_name='Kowalski'
    )

if __name__ == '__main__':
    create_sample_data()