from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import render
#from rest_framework.decorators import api_view, permission_classes
#from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import render, redirect
from .forms import TruckForm, DriverForm
from .models import Truck, Driver
from dotenv import load_dotenv
import os
import openrouteservice
from django.utils import timezone
#from datetime import timedelta
from django.contrib.auth import logout
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


env_path = Path(__file__).resolve().parent.parent / 'openroute.env'
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("ORS_API_KEY")

if not api_key:
    raise ValueError("ORS_API_KEY not loaded from openroute.env.")


# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from core.sample_data import create_sample_data
import uuid
from datetime import timedelta, datetime
#import datetime

from django.forms import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404

from core.models import Order, Hub, ProductRoute, Truck
from geopy.distance import geodesic
import json


def sample_data(request):
    create_sample_data()
    return JsonResponse({'status': 'ok'})

@login_required
def home(request):
    return render(request, 'home.html')


class CustomLoginView(LoginView):
    template_name = 'login.html'

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')  # Przekierowanie po wylogowaniu



@login_required
def delete_order(request, order_id):
    if request.method == 'DELETE':
        order = get_object_or_404(Order, id=order_id)
        order.delete()
        return JsonResponse({'success': True, 'message': 'Produkt usunięty'})
    return JsonResponse({'success': False, 'error': 'Nieprawidłowe żądanie'}, status=400)

@login_required
def manage_hub_lorries(request, hub_id):
    hub = get_object_or_404(Hub, id=hub_id)
    assigned_lorries = hub.trucks.all()
    # Wyklucz ciężarówki, które są przypisane do jakiegokolwiek huba
    assigned_truck_ids = Hub.trucks.through.objects.values_list('truck_id', flat=True)
    available_lorries = Truck.objects.exclude(id__in=assigned_truck_ids)

    return render(request, 'manage_hub_lorries.html', {
        'hub': hub,
        'assigned_lorries': assigned_lorries,
        'available_lorries': available_lorries
    })



def generate_routes_view(request):
    if request.method == "POST":
        orders = Order.objects.all()
        truck_capacity = 1000

        routes = combine_orders(orders, truck_capacity)
        print(routes)

        for route_info in routes:
            common_segment = route_info["common_segment"]  # wspólny segment (lista hubów)
            for order_id in route_info["order_ids"]:
                try:
                    product = Order.objects.get(id=order_id)
                    ProductRoute.objects.update_or_create(
                        product=product,
                        defaults={"route": common_segment}
                    )
                except Order.DoesNotExist:
                    continue

        return render(request, "generate_routes.html", {"routes": routes})
    else:
        return render(request, "generate_routes.html")

def parse_time(time_str):
    return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

def parse_timedelta(td_input):

    if isinstance(td_input, (int, float)):
        return timedelta(seconds=td_input)
    elif isinstance(td_input, str):
        try:
            h, m, s = map(int, td_input.split(":"))
            return timedelta(hours=h, minutes=m, seconds=s)
        except Exception:
            return timedelta(0)
    else:
        return timedelta(0)


def get_available_lorry(hub_instance):

    available = hub_instance.trucks.all()
    if available.exists():
        return available.first()
    return None



def find_common_segments(routeA, routeB):

    segments = []
    lenA = len(routeA)
    lenB = len(routeB)

    for i in range(lenA):
        for j in range(lenB):
            if routeA[i]["hub"]["id"] != routeB[j]["hub"]["id"]:
                continue
            length = 1
            while (i + length < lenA) and (j + length < lenB) and \
                    (routeA[i + length]["hub"]["id"] == routeB[j + length]["hub"]["id"]):
                length += 1
            segments.append((i, j, length))
    return segments


def can_combine_on_segment(routeA, routeB, segment_startA, segment_startB, segment_length, volumeA, volumeB, truck_capacity):

    if volumeA + volumeB > truck_capacity or segment_length == 1:
        return False, None

    end_index_A = segment_startA + segment_length - 1
    end_index_B = segment_startB + segment_length - 1

    end_pointA = routeA[end_index_A]
    end_pointB = routeB[end_index_B]

    arrivalA = parse_time(end_pointA["arrival_time"])
    arrivalB = parse_time(end_pointB["arrival_time"])
    diff = abs(arrivalA - arrivalB)

    limit = parse_timedelta(end_pointA["time_diff"])
    if diff >= limit:
        return False, None

    from core.models import Hub
    hub_instance = Hub.objects.get(id=end_pointA["hub"]["id"])
    if hub_instance.trucks.count() == 0:
        return False, None


    common_segment = [routeA[max(segment_startA, segment_startB) + k]["hub"] for k in range(segment_length)]

    return True, common_segment


def combine_orders(orders, truck_capacity):

    combined_groups = []
    used = set()
    n = len(orders)
    for i in range(n):
        orderA = orders[i]
        if orderA.id in used:
            continue
        routesA = json.loads(orderA.all_combinations)

        group = [orderA]
        best_common_segment = None
        join_hub_id = None
        separation_hub_id = None

        for j in range(i + 1, n):
            orderB = orders[j]
            if orderB.id in used:
                continue

            routesB = json.loads(orderB.all_combinations)
            found_segment = None

            for routeA in routesA:
                for routeB in routesB:
                    segments = find_common_segments(routeA, routeB)
                    for seg in segments:
                        seg_startA, seg_startB, seg_length = seg
                        ok, common_seg = can_combine_on_segment(
                            routeA, routeB, seg_startA, seg_startB, seg_length,
                            orderA.volume, orderB.volume, truck_capacity
                        )
                        if ok:
                            if not best_common_segment or len(common_seg) < len(best_common_segment):
                                found_segment = common_seg
                            else:
                                found_segment = best_common_segment
                            join_hub_id = common_seg[0]["id"]
                            separation_hub_id = common_seg[-1]["id"]
                            break
                    if found_segment:
                        break
                if found_segment:
                    break

            if found_segment:
                group.append(orderB)
                used.add(orderB.id)
                best_common_segment = found_segment

        if len(group) > 1:
            used.add(orderA.id)
            combined_groups.append({
                "order_ids": [o.id for o in group],
                "common_segment": best_common_segment,
                "total_volume": sum(o.volume for o in group)
            })

            from core.models import Hub, Truck

            join_hub_instance = Hub.objects.get(id=join_hub_id)
            if any(order.current_hub.id != join_hub_id for order in group):
                lorry = get_available_lorry(join_hub_instance)
                if lorry:
                    join_hub_instance.trucks.add(lorry)
                    join_hub_instance.save()

            separation_hub_instance = Hub.objects.get(id=separation_hub_id)
            if any(order.destination_hub.id != separation_hub_id for order in group):
                if separation_hub_instance.trucks.exists():
                    lorry = separation_hub_instance.trucks.first()
                    separation_hub_instance.trucks.remove(lorry)
                    separation_hub_instance.save()
    return combined_groups





def get_travel_time(coord1, coord2, api_key):

    client = openrouteservice.Client(key=api_key)


    try:
        route = client.directions(
            coordinates=[coord1, coord2],
            profile='driving-hgv',
            format='json',
            radiuses=[8000, 8000],
            validate=True,
            extra_params={'options': {'vehicle_type': 'truck'}},
        )

        duration_sec = route['routes'][0]['summary']['duration']
        return timedelta(seconds=duration_sec)

    except Exception as e:
        print("Error fetching route:", e)
        return None


# dodać czas przeładowania
def find_valid_routes(start_hub, destination_hub, deadline, start_time, visited=None, arrival_time=None):

    if visited is None:
        visited = []

    if arrival_time is None:
        arrival_time = start_time

    time_diff = deadline - arrival_time

    total_seconds = int(time_diff.total_seconds())
    if total_seconds < 0:
        total_seconds = 0
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    time_diff_str = f"{hours:02}:{minutes:02}:{seconds:02}"

    visited.append({
        'hub': model_to_dict(start_hub, fields=['id', 'name', 'location_latitude', 'location_longitude']),
        'arrival_time': arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
        'time_diff': time_diff_str
    })

    if start_hub == destination_hub:
        return [visited.copy()]

    valid_routes = []

    for next_hub in Hub.objects.exclude(id=start_hub.id):
        if next_hub in visited:
            continue

        travel_time0 = get_travel_time(
            (start_hub.location_longitude, start_hub.location_latitude),
            (destination_hub.location_longitude, destination_hub.location_latitude),
            api_key
        )


        travel_time1 = get_travel_time(
            (start_hub.location_longitude, start_hub.location_latitude),
            (next_hub.location_longitude, next_hub.location_latitude),
            api_key
        )

        if next_hub.location_longitude != destination_hub.location_longitude:
            travel_time2 = get_travel_time(
                (next_hub.location_longitude, next_hub.location_latitude),
                (destination_hub.location_longitude, destination_hub.location_latitude),
                api_key
            )
        else:
            travel_time2 = timedelta(seconds=0)



        new_deadline = deadline - travel_time1
        new_arrival_time = arrival_time + travel_time1
        if deadline - travel_time1 - travel_time2 >= start_time and travel_time0 > travel_time2:
            valid_routes.extend(find_valid_routes(next_hub, destination_hub, new_deadline, start_time, visited.copy(), new_arrival_time))

    return valid_routes


def addHub(name, location_latitude, location_longitude):
    Hub.objects.create(name=name, location_latitude=location_latitude, location_longitude=location_longitude)


def addProduct(order_number, name, volume, priority, current_hub, destination_hub, start_time):
    travel_time = get_travel_time(
        (current_hub.location_longitude, current_hub.location_latitude),
        (destination_hub.location_longitude, destination_hub.location_latitude),
        api_key
    )
    start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M")

    if priority == 1:
        deadline = start_time + travel_time + timedelta(hours=48)
    elif priority == 2:
        deadline = start_time + travel_time + timedelta(hours=24)
    else:
        deadline = start_time + travel_time

    all_combinations = find_valid_routes(current_hub, destination_hub, deadline, start_time)

    all_combinations_json = json.dumps(all_combinations, separators=(",", ":"))

    Order.objects.create(order_number=order_number, name=name, volume=volume, priority=priority, current_hub=current_hub,
                           destination_hub=destination_hub, deadline=deadline, will_arrive_current_hub_at=start_time,
                           all_combinations=all_combinations_json)

def product_form(request):
    if request.method == "POST":
        order_number = str(uuid.uuid4())[:20]
        name = request.POST["name"]
        volume = int(request.POST["volume"])
        priority = int(request.POST["priority"])
        current_hub = Hub.objects.get(id=int(request.POST["current_hub"]))
        destination_hub = Hub.objects.get(id=int(request.POST["destination_hub"]))
        start_time = request.POST["start_time"]
        addProduct(order_number, name, volume, priority, current_hub, destination_hub, start_time)
        return redirect("/products")

    hubs = Hub.objects.all()
    return render(request, "product_form.html", {"hubs": hubs})

def hub_form(request):
    if request.method == "POST":
        name = request.POST["name"]
        location_latitude = float(request.POST["location_latitude"])
        location_longitude = float(request.POST["location_longitude"])
        addHub(name, location_latitude, location_longitude)
        return redirect("/hubs")

    return render(request, "hub_form.html")

def product_list(request):
    products = Order.objects.all()
    return render(request, "product_list.html", {"products": products})


from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from .models import Order
#import datetime

def generate_report(request, order_id):
    order = Order.objects.get(id=order_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="raport_{order.id}.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    # Nagłówek
    p.setFont("Helvetica-Bold", 20)
    p.drawString(220, height - 50, "Raport Zamówienia")
    p.line(100, height - 60, 500, height - 60)  # Pozioma linia pod nagłówkiem

    # Dane do tabeli
    data = [
        ["ID Zamówienia", str(order.id)],
        ["Nazwa produktu", order.name],
        ["Objetosc", f"{order.volume} m³"],
        ["Priorytet", order.priority],
        ["Obecny Hub", order.current_hub.name],
        ["Docelowy Hub", order.destination_hub.name],
        ["Deadline", order.deadline],
        ["Status", "Dostarczone"]
    ]

    # Dodanie informacji o kierowcy, jeśli przypisany
    if hasattr(order, "driver") and order.driver:
        data.append(["Kierowca", f"{order.driver.name} ({order.driver.license_number})"])

    # Dodanie informacji o ciężarówce, jeśli przypisana
    if hasattr(order, "truck") and order.truck:
        data.append(["Ciężarówka", f"{order.truck.brand} {order.truck.model}, Ładowność: {order.truck.capacity} kg"])

    # Tworzenie tabeli z mniejszymi kolumnami
    table = Table(data, colWidths=[150, 250])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),  # Nagłówek tabeli na szaro
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    table.wrapOn(p, 100, height - 300)
    table.drawOn(p, 100, height - 300)

    # Stopka z datą wygenerowania raportu
    p.setFont("Helvetica-Oblique", 10)
    #p.drawString(100, 50, f"Data wygenerowania raportu: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")

    p.showPage()
    p.save()

    return response




def manage_hub_lorries(request, hub_id):
    hub = get_object_or_404(Hub, id=hub_id)
    assigned_lorries = hub.trucks.all()
    available_lorries = Truck.objects.exclude(id__in=assigned_lorries.values_list('id', flat=True))

    return render(request, 'manage_hub_lorries.html', {
        'hub': hub,
        'assigned_lorries': assigned_lorries,
        'available_lorries': available_lorries
    })

def add_lorry_to_hub(request, hub_id):
    hub = get_object_or_404(Hub, id=hub_id)

    if request.method == 'POST':
        lorry_id = request.POST.get('lorry_id')
        lorry = get_object_or_404(Truck, id=lorry_id)
        hub.trucks.add(lorry)
        return redirect('manage_hub_lorries', hub_id=hub.id)

    return redirect('manage_hub_lorries', hub_id=hub.id)

def remove_lorry_from_hub(request, hub_id):
    hub = get_object_or_404(Hub, id=hub_id)

    if request.method == 'POST':
        lorry_id = request.POST.get('lorry_id')
        lorry = get_object_or_404(Truck, id=lorry_id)
        hub.trucks.remove(lorry)
        return redirect('manage_hub_lorries', hub_id=hub.id)

    return redirect('manage_hub_lorries', hub_id=hub.id)

def add_lorry(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        trailer_volume = request.POST.get('trailer_volume')

        if name and trailer_volume:
            Truck.objects.create(registration_number=str(uuid.uuid4())[:20], brand=name, capacity=int(trailer_volume))
            return redirect('add_lorry')

    return render(request, 'add_lorry.html')


@login_required
def add_truck(request):
    if request.method == 'POST':
        form = TruckForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('truck_list')  # Przekierowanie na listę ciężarówek
    else:
        form = TruckForm()
    
    return render(request, 'add_truck.html', {'form': form})


@login_required
def truck_list(request):
    trucks = Truck.objects.all()

    if request.method == 'POST':
        truck_id = request.POST.get('truck_id')
        action = request.POST.get('action')

        if action == 'delete':
            truck = get_object_or_404(Truck, id=truck_id)
            truck.delete()
            return JsonResponse({'success': True, 'message': 'Ciężarówka usunięta'})

        return JsonResponse({'success': False, 'error': 'Nieprawidłowe działanie'}, status=400)

    return render(request, 'truck_list.html', {'trucks': trucks})
def hub_list(request):
    hubs = Hub.objects.all()
    return render(request, 'hub_list.html', {'hubs': hubs})
@login_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES).keys():
            order.status = new_status
            order.save()
            return JsonResponse({'success': True, 'message': 'Status updated'})
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

@login_required
def driver_list(request):
    drivers = Driver.objects.all()

    if request.method == 'POST':
        driver_id = request.POST.get('driver_id')
        action = request.POST.get('action')

        driver = get_object_or_404(Driver, id=driver_id)

        if action == 'delete':
            driver.delete()
            return JsonResponse({'success': True, 'message': 'Kierowca usunięty'})

        return redirect('driver_list')

    return render(request, 'driver_list.html', {'drivers': drivers})
@login_required
def add_driver(request):
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('driver_list')
    else:
        form = DriverForm()
    return render(request, 'add_driver.html', {'form': form})

@login_required
def manage_driver_trucks(request, driver_id):
    driver = get_object_or_404(Driver, id=driver_id)
    assigned_trucks = Order.objects.filter(driver=driver).values_list('truck', flat=True).distinct()
    assigned_trucks = Truck.objects.filter(id__in=assigned_trucks)

    assigned_truck_ids = Order.objects.exclude(driver__isnull=True).values_list('truck', flat=True).distinct()
    available_trucks = Truck.objects.exclude(id__in=assigned_truck_ids)

    if request.method == 'POST':
        truck_id = request.POST.get('truck_id')
        action = request.POST.get('action')

        truck = get_object_or_404(Truck, id=truck_id)

        if action == 'assign':
            order = Order.objects.filter(truck=truck, driver__isnull=True).first()
            if not order:
                default_hub = Hub.objects.first()
                if not default_hub:
                    return JsonResponse({'success': False, 'error': 'Brak hubów w systemie'}, status=400)
                order = Order.objects.create(
                    truck=truck,
                    driver=driver,
                    status='pending',
                    name=f"Zamówienie dla {truck.registration_number}",
                    volume=1,
                    priority=1,
                    deadline=timezone.now() + timedelta(days=7),
                    current_hub=default_hub,
                    destination_hub=default_hub,
                    will_arrive_current_hub_at=timezone.now(),
                    order_number=str(uuid.uuid4())[:8],
                    all_combinations=[]
                )
            else:
                order.driver = driver
                order.save()
        elif action == 'unassign':
            Order.objects.filter(driver=driver, truck=truck).update(driver=None)

        return redirect('manage_driver_trucks', driver_id=driver.id)

    return render(request, 'manage_driver_trucks.html', {
        'driver': driver,
        'assigned_trucks': assigned_trucks,
        'available_trucks': available_trucks
    })

@login_required
def manage_trucks(request):
    trucks = Truck.objects.all()
    hubs = Hub.objects.all()

    if request.method == 'POST':
        truck_id = request.POST.get('truck_id')
        hub_id = request.POST.get('hub_id')
        action = request.POST.get('action')

        truck = get_object_or_404(Truck, id=truck_id)
        hub = get_object_or_404(Hub, id=hub_id) if hub_id else None

        if action == 'assign':
            hub.trucks.add(truck)
        elif action == 'unassign':
            hub.trucks.remove(truck)

        return redirect('manage_trucks')

    return render(request, 'manage_trucks.html', {
        'trucks': trucks,
        'hubs': hubs
    })