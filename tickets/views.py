from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.views.generic import DetailView, ListView

from accounts.models import User
from accounts.permissions import RoleRequiredMixin, role_required

from . import services
from .forms import TicketOpenForm
from .models import Ticket


@require_http_methods(["GET", "POST"])
@role_required(User.Role.SOLICITANTE)
def ticket_create(request):
    """US1: formulário de abertura. A regra fica em ``services.open_ticket``."""
    form = TicketOpenForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            ticket = services.open_ticket(requester=request.user, **form.cleaned_data)
        except services.TicketRuleError as error:
            form.add_error(None, str(error))
        else:
            messages.success(request, f"Chamado #{ticket.pk} aberto.")
            return redirect("tickets:detail", pk=ticket.pk)
    return render(request, "tickets/ticket_form.html", {"form": form})


class VisibleTicketsMixin:
    """Toda consulta de chamado parte do que o usuário enxerga (SU03)."""

    def get_queryset(self):
        return Ticket.objects.visible_to(self.request.user).select_related(
            "location", "category", "technician", "requester"
        )


class MyTicketListView(RoleRequiredMixin, VisibleTicketsMixin, ListView):
    """US2: "Meus chamados" do solicitante, do mais novo para o mais antigo.

    A consulta geral do coordenador é a SU09 e as ordens do técnico, a SU11.
    """

    allowed_roles = (User.Role.SOLICITANTE,)
    paginate_by = 20


class TicketDetailView(LoginRequiredMixin, VisibleTicketsMixin, DetailView):
    """Detalhe de um chamado, para qualquer papel.

    Chamado fora do ``visible_to`` do usuário dá 404: não revela que ele existe.
    """
