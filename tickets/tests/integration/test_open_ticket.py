from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from tickets.models import Ticket
from tickets.tests.factories import criar_chamado, criar_local_e_tipo, criar_usuario

Role = User.Role


class AbrirChamadoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = criar_usuario("ana")
        cls.bia = criar_usuario("bia")
        cls.local, cls.tipo = criar_local_e_tipo()
        cls.url = reverse("tickets:create")

    def setUp(self):
        self.client.force_login(self.ana)

    def dados(self, **extra):
        return {
            "location": self.local.pk,
            "category": self.tipo.pk,
            "description": "Impressora atolando papel.",
            **extra,
        }

    def test_formulario_abre_para_o_solicitante(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tickets/ticket_form.html")
        self.assertContains(response, self.local.name)

    def test_envio_valido_cria_chamado_e_mostra_o_detalhe_com_confirmacao(self):
        response = self.client.post(self.url, self.dados(), follow=True)
        ticket = Ticket.objects.get()
        self.assertRedirects(response, reverse("tickets:detail", args=[ticket.pk]))
        self.assertContains(response, f"Chamado #{ticket.pk} aberto.")
        self.assertEqual(ticket.requester, self.ana)
        self.assertEqual(ticket.status, Ticket.Status.ABERTO)

    def test_solicitante_forjado_no_post_e_ignorado(self):
        self.client.post(
            self.url, self.dados(requester=self.bia.pk, status=Ticket.Status.CONCLUIDO)
        )
        ticket = Ticket.objects.get()
        self.assertEqual(ticket.requester, self.ana)
        self.assertEqual(ticket.status, Ticket.Status.ABERTO)

    def test_sem_local_ou_descricao_mostra_erro_e_nao_grava(self):
        for campo in ("location", "description"):
            with self.subTest(campo=campo):
                response = self.client.post(self.url, self.dados(**{campo: ""}))
                self.assertEqual(response.status_code, 200)
                self.assertIn(campo, response.context["form"].errors)
                self.assertFalse(Ticket.objects.exists())

    def test_quarto_chamado_ativo_e_recusado_com_mensagem_e_nao_grava(self):
        for _ in range(3):
            criar_chamado(self.ana, self.local, self.tipo)
        response = self.client.post(self.url, self.dados())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Você já tem 3 chamados ativos.")
        self.assertEqual(Ticket.objects.count(), 3)

    def test_coordenador_e_tecnico_recebem_403_e_nada_e_gravado(self):
        for papel in (Role.COORDENADOR, Role.TECNICO):
            with self.subTest(papel=papel):
                self.client.force_login(criar_usuario(f"u-{papel.lower()}", papel))
                for metodo in (self.client.get, self.client.post):
                    response = metodo(self.url, self.dados())
                    self.assertEqual(response.status_code, 403)
                self.assertFalse(Ticket.objects.exists())

    def test_anonimo_vai_para_o_login_e_nada_e_gravado(self):
        self.client.logout()
        response = self.client.post(self.url, self.dados())
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.url}")
        self.assertFalse(Ticket.objects.exists())

    def test_painel_do_solicitante_tem_o_atalho(self):
        response = self.client.get(reverse("accounts:home"))
        self.assertContains(response, f'href="{self.url}"')
