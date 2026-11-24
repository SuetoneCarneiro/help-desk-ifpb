from django.contrib.auth import SESSION_KEY
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from tickets.models import Location

SENHA = "senha-de-teste-123"


def criar_usuario(username, role=User.Role.SOLICITANTE):
    return User.objects.create_user(username=username, password=SENHA, role=role)


class LoginTests(TestCase):
    def setUp(self):
        self.user = criar_usuario("maria")
        self.url = reverse("accounts:login")

    def test_pagina_de_login_abre_para_anonimo(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "registration/login.html")

    def test_credenciais_validas_abrem_sessao_e_levam_ao_painel(self):
        response = self.client.post(self.url, {"username": "maria", "password": SENHA})
        self.assertRedirects(response, reverse("accounts:home"))
        self.assertEqual(int(self.client.session[SESSION_KEY]), self.user.pk)

    def test_senha_errada_mostra_erro_e_nao_abre_sessao(self):
        response = self.client.post(self.url, {"username": "maria", "password": "x"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_usuario_inativo_nao_entra(self):
        self.user.is_active = False
        self.user.save()
        self.client.post(self.url, {"username": "maria", "password": SENHA})
        self.assertNotIn(SESSION_KEY, self.client.session)

    def test_respeita_o_next(self):
        response = self.client.post(
            f"{self.url}?next=/admin/",
            {"username": "maria", "password": SENHA, "next": "/admin/"},
        )
        self.assertRedirects(response, "/admin/", fetch_redirect_response=False)

    def test_next_externo_e_ignorado(self):
        response = self.client.post(
            self.url,
            {"username": "maria", "password": SENHA, "next": "https://exemplo.com/"},
        )
        self.assertRedirects(response, reverse("accounts:home"))

    def test_quem_ja_esta_logado_nao_ve_o_login_de_novo(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("accounts:home"))


class LogoutTests(TestCase):
    def setUp(self):
        self.user = criar_usuario("maria")
        self.client.force_login(self.user)
        self.url = reverse("accounts:logout")

    def test_logout_por_get_e_recusado_e_mantem_a_sessao(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertIn(SESSION_KEY, self.client.session)

    def test_logout_por_post_encerra_a_sessao(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse("accounts:login"))
        self.assertNotIn(SESSION_KEY, self.client.session)


class PainelTests(TestCase):
    def test_anonimo_e_mandado_para_o_login(self):
        response = self.client.get(reverse("accounts:home"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next=/")

    def test_painel_identifica_o_papel_de_quem_entrou(self):
        casos = {
            User.Role.SOLICITANTE: "Solicitante",
            User.Role.COORDENADOR: "Coordenador de TI",
            User.Role.TECNICO: "Técnico de TI",
        }
        for papel, rotulo in casos.items():
            with self.subTest(papel=papel):
                self.client.force_login(criar_usuario(f"u-{papel.lower()}", papel))
                response = self.client.get(reverse("accounts:home"))
                self.assertContains(response, f"<strong>{rotulo}</strong>", html=True)
                self.assertEqual(response.context["user"].role, papel)


@override_settings(ROOT_URLCONF="accounts.tests.integration.urls")
class RotaRestritaPorPapelTests(TestCase):
    """O 403 precisa sair antes de qualquer gravação no banco."""

    def setUp(self):
        self.url = reverse("criar-local")

    def test_anonimo_vai_para_o_login_e_nada_e_gravado(self):
        response = self.client.post(self.url, {"name": "Lab 1"})
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={self.url}",
            fetch_redirect_response=False,
        )
        self.assertFalse(Location.objects.exists())

    def test_papel_errado_recebe_403_e_nada_e_gravado(self):
        for papel in (User.Role.SOLICITANTE, User.Role.TECNICO):
            with self.subTest(papel=papel):
                self.client.force_login(criar_usuario(f"u-{papel.lower()}", papel))
                response = self.client.post(self.url, {"name": "Lab 1"})
                self.assertEqual(response.status_code, 403)
                self.assertContains(response, "Acesso negado", status_code=403)
                self.assertFalse(Location.objects.exists())

    def test_papel_certo_grava(self):
        self.client.force_login(criar_usuario("coord", User.Role.COORDENADOR))
        response = self.client.post(self.url, {"name": "Lab 1"})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Location.objects.filter(name="Lab 1").exists())
