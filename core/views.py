from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import render
#from rest_framework.decorators import api_view, permission_classes
#from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import render, redirect
from .forms import TruckForm
from .models import Truck

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

#from core.sample_data import create_sample_data
import uuid
from datetime import timedelta, datetime

from django.forms import model_to_dict
from django.shortcuts import render, redirect, get_object_or_404

from core.models import Order, Hub, ProductRoute, Truck
from geopy.distance import geodesic
import json
"""
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sample_data(request):
    create_sample_data()
    return JsonResponse({'status': 'ok'})
"""
def home(request):
    return render(request, 'home.html')


class CustomLoginView(LoginView):
    template_name = 'login.html'








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


def get_travel_time(coord1, coord2):
    # temp
    distance_km = geodesic(coord1, coord2).km
    average_speed_kmh = 70
    return timedelta(hours=distance_km / average_speed_kmh)

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
            (start_hub.location_latitude, start_hub.location_longitude),
            (destination_hub.location_latitude, destination_hub.location_longitude)
        )

        travel_time1 = get_travel_time(
            (start_hub.location_latitude, start_hub.location_longitude),
            (next_hub.location_latitude, next_hub.location_longitude)
        )

        travel_time2 = get_travel_time(
            (next_hub.location_latitude, next_hub.location_longitude),
            (destination_hub.location_latitude, destination_hub.location_longitude)
        )


        new_deadline = deadline - travel_time1
        new_arrival_time = arrival_time + travel_time1
        if deadline - travel_time1 - travel_time2 >= start_time and travel_time0 > travel_time2:
            valid_routes.extend(find_valid_routes(next_hub, destination_hub, new_deadline, start_time, visited.copy(), new_arrival_time))

    return valid_routes


def addHub(name, location_latitude, location_longitude):
    Hub.objects.create(name=name, location_latitude=location_latitude, location_longitude=location_longitude)


def addProduct(order_number, name, volume, priority, current_hub, destination_hub, start_time):
    travel_time = get_travel_time(
        (current_hub.location_latitude, current_hub.location_longitude),
        (destination_hub.location_latitude, destination_hub.location_longitude)

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



def add_truck(request):
    if request.method == 'POST':
        form = TruckForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('truck_list')  # Przekierowanie na listę ciężarówek
    else:
        form = TruckForm()
    
    return render(request, 'add_truck.html', {'form': form})

def truck_list(request):
    trucks = Truck.objects.all()
    return render(request, 'truck_list.html', {'trucks': trucks})
