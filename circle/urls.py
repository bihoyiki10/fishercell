from django.urls import path

from . import views

app_name = 'circle'

urlpatterns = [
    path('', views.home, name='home'),
]
