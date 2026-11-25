from django import forms

from .models import Ticket


class TicketOpenForm(forms.ModelForm):
    """US1: só o que o solicitante informa.

    Solicitante, status e datas não aparecem aqui: o serviço define a partir
    do usuário logado, e nada que venha no POST consegue trocá-los.
    """

    class Meta:
        model = Ticket
        fields = ("location", "category", "description")
