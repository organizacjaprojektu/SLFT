from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import TruckForm
from .models import Truck

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from core.sample_data import create_sample_data

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sample_data(request):
    create_sample_data()
    return JsonResponse({'status': 'ok'})

def home(request):
    return render(request, 'home.html')


class CustomLoginView(LoginView):
    template_name = 'login.html'



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
