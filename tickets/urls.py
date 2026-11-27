from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    path("chamados/", views.MyTicketListView.as_view(), name="list"),
    path("chamados/novo/", views.ticket_create, name="create"),
    path("chamados/<int:pk>/", views.TicketDetailView.as_view(), name="detail"),
]
