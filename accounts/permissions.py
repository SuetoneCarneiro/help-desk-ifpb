"""Verificações de papel reutilizáveis pelas views (SU02).

Duas portas para a mesma regra:

- ``role_required(*roles)`` para views em função;
- ``RoleRequiredMixin`` para views em classe.

Em ambas, o anônimo é mandado para o login (com ``?next=``) e o usuário
autenticado com papel errado recebe 403. Nenhuma das duas confia no template:
esconder um botão não impede a requisição.
"""

from functools import wraps

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ImproperlyConfigured, PermissionDenied

from .models import User


def _validate_roles(roles) -> None:
    if not roles:
        raise ValueError("Informe ao menos um papel.")
    invalid = set(roles) - set(User.Role.values)
    if invalid:
        raise ValueError(f"Papel desconhecido: {', '.join(sorted(invalid))}.")


def has_role(user, *roles) -> bool:
    """True se o usuário está autenticado e tem um dos papéis informados."""
    return user.is_authenticated and user.role in roles


def role_required(*roles):
    """Restringe uma view em função aos papéis informados."""
    _validate_roles(roles)

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if not has_role(request.user, *roles):
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


class RoleRequiredMixin(UserPassesTestMixin):
    """Restringe uma view em classe aos papéis de ``allowed_roles``.

    O ``UserPassesTestMixin`` já separa os dois casos de recusa: anônimo vai
    para o login e autenticado sem o papel recebe 403.
    """

    allowed_roles: tuple[str, ...] = ()

    def test_func(self) -> bool:
        if not self.allowed_roles:
            raise ImproperlyConfigured(
                f"{type(self).__name__} precisa definir allowed_roles."
            )
        _validate_roles(self.allowed_roles)
        return has_role(self.request.user, *self.allowed_roles)
