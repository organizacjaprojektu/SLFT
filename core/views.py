from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import render

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