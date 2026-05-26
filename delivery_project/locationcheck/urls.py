from django.urls import path
from . import views

urlpatterns = [
    path('', views.location_page, name='location_page'),
    path('check-location/', views.check_location, name='check_location'),
    path('next-step/', views.next_step, name='next_step'),
]