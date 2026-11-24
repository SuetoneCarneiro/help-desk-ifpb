from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Usuário do Help Desk. O papel define o que cada um pode ver e fazer."""

    class Role(models.TextChoices):
        SOLICITANTE = "SOLICITANTE", "Solicitante"
        COORDENADOR = "COORDENADOR", "Coordenador de TI"
        TECNICO = "TECNICO", "Técnico de TI"

    role = models.CharField(
        "papel",
        max_length=20,
        choices=Role.choices,
        default=Role.SOLICITANTE,
    )

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

    @property
    def is_solicitante(self) -> bool:
        return self.role == self.Role.SOLICITANTE

    @property
    def is_coordenador(self) -> bool:
        return self.role == self.Role.COORDENADOR

    @property
    def is_tecnico(self) -> bool:
        return self.role == self.Role.TECNICO
