"""Quem pode fazer o quê com os chamados (SU03).

Cada função responde uma pergunta de sim ou não, como "este usuário pode
cancelar este chamado?". Telas e serviços consultam estas funções em vez de
repetir a checagem. A matriz completa está em ``docs/plano-su03-permissoes.md``.

Aqui fica só o **quem**. O **quando** (status certo, limite de 5 ordens,
descrição com 20 caracteres) é regra de negócio e fica em ``tickets/services.py``.
"""

from django.core.exceptions import PermissionDenied

from accounts.models import User
from accounts.permissions import has_role

Role = User.Role


def ensure(
    allowed: bool, message: str = "Você não tem permissão para esta operação."
) -> None:
    """Transforma um "não" das políticas em ``PermissionDenied`` (resposta 403)."""
    if not allowed:
        raise PermissionDenied(message)


# --- Operações que dependem só do papel -------------------------------------


def can_open_ticket(user) -> bool:
    """US1: só o solicitante abre chamado."""
    return has_role(user, Role.SOLICITANTE)


def can_assign_ticket(user) -> bool:
    """US4: só o coordenador atribui técnico e prioridade."""
    return has_role(user, Role.COORDENADOR)


def can_refuse_ticket(user) -> bool:
    """US5: só o coordenador recusa chamado."""
    return has_role(user, Role.COORDENADOR)


def can_view_all_tickets(user) -> bool:
    """US6: consulta geral e atrasados são do coordenador."""
    return has_role(user, Role.COORDENADOR)


def can_view_reports(user) -> bool:
    """US7: relatório de produtividade é do coordenador."""
    return has_role(user, Role.COORDENADOR)


# --- Operações que dependem do papel e do chamado ----------------------------


def _is_requester(user, ticket) -> bool:
    return has_role(user, Role.SOLICITANTE) and ticket.requester_id == user.pk


def _is_assigned_technician(user, ticket) -> bool:
    return has_role(user, Role.TECNICO) and ticket.technician_id == user.pk


def can_view_ticket(user, ticket) -> bool:
    """US2/US8: o dono, o técnico designado e o coordenador.

    Precisa concordar com ``Ticket.objects.visible_to(user)``; há um teste que
    compara as duas.
    """
    return (
        has_role(user, Role.COORDENADOR)
        or _is_requester(user, ticket)
        or _is_assigned_technician(user, ticket)
    )


def can_cancel_ticket(user, ticket) -> bool:
    """US3: só o solicitante dono do chamado."""
    return _is_requester(user, ticket)


def can_start_ticket(user, ticket) -> bool:
    """US9 (Recusa 2): só o técnico designado inicia o atendimento."""
    return _is_assigned_technician(user, ticket)


def can_complete_ticket(user, ticket) -> bool:
    """US10: só o técnico designado conclui a ordem."""
    return _is_assigned_technician(user, ticket)
