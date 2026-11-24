from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    """Painel provisório: mostra quem está logado e com qual papel.

    Nos próximos cards, cada papel passa a cair na própria fila de chamados.
    """
    return render(request, "accounts/home.html")
