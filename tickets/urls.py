from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    path("chamados/novo/", views.ticket_create, name="create"),
]
