"""URLconf usada só nos testes: uma view restrita que altera o banco.

Serve para provar que o 403 sai antes de qualquer gravação. As views reais
com papel entram a partir da SU03.
"""

from django.http import HttpResponse
from django.urls import include, path

from accounts.models import User
from accounts.permissions import role_required
from tickets.models import Location


@role_required(User.Role.COORDENADOR)
def criar_local(request):
    Location.objects.create(name=request.POST["name"])
    return HttpResponse("criado", status=201)


urlpatterns = [
    path("", include("accounts.urls")),
    path("", include("tickets.urls")),
    path("teste/criar-local/", criar_local, name="criar-local"),
]
