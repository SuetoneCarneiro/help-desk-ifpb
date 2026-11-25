"""Ajudantes para montar dados de teste dos chamados."""

from accounts.models import User
from tickets.models import Category, Location, Ticket

SENHA = "senha-de-teste-123"

# Status que exigem técnico e prioridade (CheckConstraint do model).
EM_ATENDIMENTO = (
    Ticket.Status.ATRIBUIDO,
    Ticket.Status.EM_ANDAMENTO,
    Ticket.Status.CONCLUIDO,
)


def criar_usuario(username, role=User.Role.SOLICITANTE):
    return User.objects.create_user(username=username, password=SENHA, role=role)


def criar_local_e_tipo():
    return (
        Location.objects.create(name="Bloco A — Lab 1"),
        Category.objects.create(name="Computador"),
    )


def criar_chamado(
    requester, location, category, status=Ticket.Status.ABERTO, technician=None
):
    extra = {}
    if status in EM_ATENDIMENTO:
        extra = {"technician": technician, "priority": Ticket.Priority.MEDIA}
    return Ticket.objects.create(
        requester=requester,
        location=location,
        category=category,
        description="Computador não liga.",
        status=status,
        **extra,
    )
