from datetime import datetime, timedelta
from types import MappingProxyType

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Location(models.Model):
    """Local do campus onde o problema acontece (bloco, sala, laboratório)."""

    name = models.CharField("nome", max_length=100, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "local"
        verbose_name_plural = "locais"

    def __str__(self) -> str:
        return self.name


class Category(models.Model):
    """Tipo de equipamento ou categoria de atendimento."""

    name = models.CharField("nome", max_length=100, unique=True)

    class Meta:
        ordering = ("name",)
        verbose_name = "tipo de equipamento"
        verbose_name_plural = "tipos de equipamento"

    def __str__(self) -> str:
        return self.name


class TicketStatus(models.TextChoices):
    ABERTO = "ABERTO", "Aberto"
    ATRIBUIDO = "ATRIBUIDO", "Atribuído"
    EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
    CONCLUIDO = "CONCLUIDO", "Concluído"
    CANCELADO = "CANCELADO", "Cancelado"
    RECUSADO = "RECUSADO", "Recusado"


class TicketPriority(models.IntegerChoices):
    BAIXA = 1, "Baixa"
    MEDIA = 2, "Média"
    ALTA = 3, "Alta"
    URGENTE = 4, "Urgente"


class TicketQuerySet(models.QuerySet):
    def active(self):
        """Chamados que ainda ocupam a fila (US1: limite por solicitante)."""
        return self.filter(status__in=Ticket.ACTIVE_STATUSES)

    def technician_load(self):
        """Ordens que contam na carga do técnico (US4: Recusa 1)."""
        return self.filter(status__in=Ticket.TECHNICIAN_LOAD_STATUSES)

    def overdue(self, now: datetime | None = None):
        """Ordens em atendimento com prazo vencido (US6)."""
        now = now or timezone.now()
        return self.technician_load().filter(due_at__lt=now)

    def visible_to(self, user):
        """Chamados que o usuário pode ver (SU03).

        Coordenador vê todos; solicitante, os que abriu; técnico, os atribuídos
        a ele. Anônimo ou papel desconhecido não vê nada. Precisa concordar com
        ``tickets.policies.can_view_ticket``.
        """
        if not user.is_authenticated:
            return self.none()
        if user.is_coordenador:
            return self.all()
        if user.is_solicitante:
            return self.filter(requester=user)
        if user.is_tecnico:
            return self.filter(technician=user)
        return self.none()


class Ticket(models.Model):
    """Chamado de TI. Depois de atribuído, é a ordem de serviço do técnico."""

    Status = TicketStatus
    Priority = TicketPriority

    ACTIVE_STATUSES = (Status.ABERTO, Status.ATRIBUIDO, Status.EM_ANDAMENTO)
    TECHNICIAN_LOAD_STATUSES = (Status.ATRIBUIDO, Status.EM_ANDAMENTO)
    CANCELLABLE_STATUSES = (Status.ABERTO, Status.ATRIBUIDO)

    DEADLINE_BY_PRIORITY = MappingProxyType(
        {
            Priority.URGENTE: timedelta(hours=4),
            Priority.ALTA: timedelta(hours=24),
            Priority.MEDIA: timedelta(hours=72),
            Priority.BAIXA: timedelta(hours=120),
        }
    )

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_tickets",
        verbose_name="solicitante",
    )
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_tickets",
        verbose_name="técnico responsável",
        null=True,
        blank=True,
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="local",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="tipo de equipamento",
    )
    description = models.TextField("descrição do problema")

    status = models.CharField(
        "status",
        max_length=20,
        choices=Status.choices,
        default=Status.ABERTO,
    )
    priority = models.PositiveSmallIntegerField(
        "prioridade",
        choices=Priority.choices,
        null=True,
        blank=True,
    )
    due_at = models.DateTimeField("prazo", null=True, blank=True)

    refusal_reason = models.TextField("motivo da recusa", blank=True)
    resolution = models.TextField("descrição do atendimento", blank=True)

    created_at = models.DateTimeField("aberto em", auto_now_add=True)
    updated_at = models.DateTimeField("atualizado em", auto_now=True)
    assigned_at = models.DateTimeField("atribuído em", null=True, blank=True)
    started_at = models.DateTimeField("iniciado em", null=True, blank=True)
    completed_at = models.DateTimeField("concluído em", null=True, blank=True)
    canceled_at = models.DateTimeField("cancelado em", null=True, blank=True)
    refused_at = models.DateTimeField("recusado em", null=True, blank=True)

    objects = TicketQuerySet.as_manager()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "chamado"
        verbose_name_plural = "chamados"
        indexes = (
            models.Index(fields=["status"], name="ticket_status_idx"),
            models.Index(
                fields=["technician", "status"], name="ticket_tecnico_status_idx"
            ),
            models.Index(
                fields=["requester", "status"], name="ticket_solicit_status_idx"
            ),
        )
        constraints = (
            # Atribuído, em andamento ou concluído sempre tem responsável e prioridade.
            models.CheckConstraint(
                condition=(
                    Q(
                        status__in=[
                            TicketStatus.ABERTO,
                            TicketStatus.CANCELADO,
                            TicketStatus.RECUSADO,
                        ]
                    )
                    | Q(technician__isnull=False, priority__isnull=False)
                ),
                name="ticket_atendimento_exige_tecnico_e_prioridade",
            ),
        )

    def __str__(self) -> str:
        return f"#{self.pk} — {self.category} em {self.location}"

    @classmethod
    def deadline_for(cls, priority: int, start: datetime) -> datetime:
        """Prazo de atendimento a partir da atribuição, conforme a prioridade."""
        return start + cls.DEADLINE_BY_PRIORITY[cls.Priority(priority)]

    def is_overdue(self, now: datetime | None = None) -> bool:
        """Em atendimento e com o prazo vencido (US6)."""
        if self.status not in self.TECHNICIAN_LOAD_STATUSES or self.due_at is None:
            return False
        return self.due_at < (now or timezone.now())
