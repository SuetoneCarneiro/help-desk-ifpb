from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from accounts.models import User
from accounts.permissions import role_required

from . import services
from .forms import TicketOpenForm


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
            return redirect("accounts:home")
    return render(request, "tickets/ticket_form.html", {"form": form})
