from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class FrontendLayoutTests(TestCase):
    def test_login_exibe_layout_publico(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')
        self.assertNotContains(response, 'id="account-menu"')

    def test_painel_exibe_navegacao_do_papel(self):
        for role in (
            User.Role.SOLICITANTE,
            User.Role.COORDENADOR,
            User.Role.TECNICO,
        ):
            with self.subTest(role=role):
                user = User.objects.create_user(username=f"user-{role}", role=role)
                self.client.force_login(user)

                response = self.client.get(reverse("accounts:home"))

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'aria-label="Navegação principal"')
                self.assertContains(response, 'aria-current="page"')
                self.assertContains(response, f'action="{reverse("accounts:logout")}"')

                for route in ("tickets:create", "tickets:list"):
                    link = f'href="{reverse(route)}"'
                    if role == User.Role.SOLICITANTE:
                        self.assertContains(response, link)
                    else:
                        self.assertNotContains(response, link)
