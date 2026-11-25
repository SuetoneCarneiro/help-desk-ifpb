"""Regras de negócio e transições de status dos chamados.

Cada serviço segue a mesma ordem:

1. **Quem** pode: ``ensure(can_...)`` das políticas → ``PermissionDenied`` (403).
2. **Quando** pode: regra de negócio → ``TicketRuleError``, com a mensagem que a
   tela mostra ao usuário.
3. Grava.

A view só chama o serviço e traduz a exceção. Assim a regra vale igual para
qualquer porta de entrada (tela, admin, shell ou API).
"""

from django.db import transaction

from accounts.models import User

from .models import Ticket
from .policies import can_open_ticket, ensure


class TicketRuleError(Exception):
    """Uma regra de negócio recusou a operação. A mensagem vai para o usuário."""


def open_ticket(*, requester, location, category, description: str) -> Ticket:
    """US1: o solicitante abre um chamado, que nasce ``ABERTO``.

    Recusa sem local, sem tipo de equipamento ou sem descrição, e quando o
    solicitante já tem ``Ticket.MAX_ACTIVE_PER_REQUESTER`` chamados ativos.
    """
    ensure(can_open_ticket(requester), "Só solicitantes podem abrir chamados.")

    description = (description or "").strip()
    if location is None or category is None or not description:
        raise TicketRuleError(
            "Informe o local, o tipo de equipamento e a descrição do problema."
        )

    with transaction.atomic():
        # Trava o solicitante: dois envios ao mesmo tempo não passam juntos pela
        # contagem. No SQLite as escritas já são serializadas; no PostgreSQL é
        # esta trava que garante.
        User.objects.select_for_update().get(pk=requester.pk)
        active = Ticket.objects.filter(requester=requester).active().count()
        if active >= Ticket.MAX_ACTIVE_PER_REQUESTER:
            raise TicketRuleError(
                f"Você já tem {Ticket.MAX_ACTIVE_PER_REQUESTER} chamados ativos. "
                "Aguarde a conclusão de um deles ou cancele algum para abrir outro."
            )
        return Ticket.objects.create(
            requester=requester,
            location=location,
            category=category,
            description=description,
        )
