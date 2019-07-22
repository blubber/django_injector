from django.urls import path

from . import views

urlpatterns = [
    path('inject-works', views.inject_works),
]
