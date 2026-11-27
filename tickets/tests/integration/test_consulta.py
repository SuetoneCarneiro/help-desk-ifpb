from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from tickets.models import Ticket
from tickets.tests.factories import criar_chamado, criar_local_e_tipo, criar_usuario

Role = User.Role
Status = Ticket.Status


class ConsultaBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = criar_usuario("ana")
        cls.bia = criar_usuario("bia")
        cls.coord = criar_usuario("coord", Role.COORDENADOR)
        cls.tec1 = criar_usuario("tec1", Role.TECNICO)
        cls.tec2 = criar_usuario("tec2", Role.TECNICO)
        cls.local, cls.tipo = criar_local_e_tipo()
        cls.da_ana = criar_chamado(cls.ana, cls.local, cls.tipo)
        cls.da_ana_com_tec1 = criar_chamado(
            cls.ana, cls.local, cls.tipo, Status.ATRIBUIDO, cls.tec1
        )
        cls.da_bia = criar_chamado(cls.bia, cls.local, cls.tipo)


class MeusChamadosTests(ConsultaBase):
    url = reverse("tickets:list")

    def test_solicitante_ve_so_os_proprios_do_mais_novo_ao_mais_antigo(self):
        self.client.force_login(self.ana)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["ticket_list"]), [self.da_ana_com_tec1, self.da_ana]
        )
        self.assertNotContains(response, f">#{self.da_bia.pk}<")

    def test_lista_mostra_tecnico_e_traco_quando_nao_ha(self):
        self.client.force_login(self.ana)
        response = self.client.get(self.url)
        self.assertContains(response, "tec1")
        self.assertContains(response, "—")

    def test_solicitante_sem_chamados_ve_aviso(self):
        self.client.force_login(criar_usuario("caio"))
        response = self.client.get(self.url)
        self.assertContains(response, "Você ainda não abriu nenhum chamado.")

    def test_pagina_de_20_em_20(self):
        for _ in range(21):
            criar_chamado(self.bia, self.local, self.tipo, Status.CONCLUIDO, self.tec1)
        self.client.force_login(self.bia)
        primeira = self.client.get(self.url)
        segunda = self.client.get(self.url, {"page": 2})
        self.assertEqual(len(primeira.context["ticket_list"]), 20)
        self.assertEqual(len(segunda.context["ticket_list"]), 2)
        self.assertContains(primeira, "Página 1 de 2")

    def test_numero_de_consultas_nao_cresce_com_a_lista(self):
        self.client.force_login(self.ana)
        with self.assertNumQueries(4) as poucos:
            self.client.get(self.url)
        for _ in range(10):
            criar_chamado(self.ana, self.local, self.tipo, Status.CONCLUIDO, self.tec2)
        with self.assertNumQueries(len(poucos.captured_queries)):
            self.client.get(self.url)

    def test_coordenador_e_tecnico_recebem_403(self):
        for user in (self.coord, self.tec1):
            with self.subTest(papel=user.role):
                self.client.force_login(user)
                self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_anonimo_vai_para_o_login(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.url}")

    def test_painel_do_solicitante_tem_o_atalho(self):
        self.client.force_login(self.ana)
        response = self.client.get(reverse("accounts:home"))
        self.assertContains(response, f'href="{self.url}"')


class DetalheTests(ConsultaBase):
    def url(self, ticket):
        return reverse("tickets:detail", args=[ticket.pk])

    def test_quem_pode_ver_recebe_200_e_os_outros_404(self):
        """Mesma matriz do can_view_ticket (SU03), agora pela requisição."""
        casos = {
            "dono": (self.ana, self.da_ana_com_tec1, 200),
            "outro solicitante": (self.bia, self.da_ana_com_tec1, 404),
            "coordenador": (self.coord, self.da_ana_com_tec1, 200),
            "técnico designado": (self.tec1, self.da_ana_com_tec1, 200),
            "outro técnico": (self.tec2, self.da_ana_com_tec1, 404),
            "técnico em chamado sem técnico": (self.tec1, self.da_ana, 404),
        }
        for caso, (user, ticket, esperado) in casos.items():
            with self.subTest(caso=caso):
                self.client.force_login(user)
                response = self.client.get(self.url(ticket))
                self.assertEqual(response.status_code, esperado)

    def test_chamado_inexistente_e_alheio_tem_a_mesma_resposta(self):
        self.client.force_login(self.bia)
        alheio = self.client.get(self.url(self.da_ana))
        inexistente = self.client.get(reverse("tickets:detail", args=[99999]))
        self.assertEqual(alheio.status_code, inexistente.status_code)

    def test_anonimo_vai_para_o_login(self):
        url = self.url(self.da_ana)
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={url}")

    def test_mostra_os_dados_do_chamado(self):
        self.client.force_login(self.ana)
        response = self.client.get(self.url(self.da_ana_com_tec1))
        for texto in (self.local.name, self.tipo.name, "Atribuído", "Média", "tec1"):
            with self.subTest(texto=texto):
                self.assertContains(response, texto)

    def test_mostra_motivo_da_recusa_e_descricao_do_atendimento(self):
        agora = timezone.now()
        recusado = criar_chamado(self.ana, self.local, self.tipo, Status.RECUSADO)
        recusado.refusal_reason = "Equipamento particular, fora do escopo da TI."
        recusado.refused_at = agora
        recusado.save()
        concluido = criar_chamado(
            self.ana, self.local, self.tipo, Status.CONCLUIDO, self.tec1
        )
        concluido.resolution = "Fonte trocada e equipamento testado."
        concluido.completed_at = agora
        concluido.save()
        self.client.force_login(self.ana)
        self.assertContains(
            self.client.get(self.url(recusado)), recusado.refusal_reason
        )
        self.assertContains(self.client.get(self.url(concluido)), concluido.resolution)

    def test_indica_atraso(self):
        self.da_ana_com_tec1.due_at = timezone.now() - timedelta(hours=1)
        self.da_ana_com_tec1.save()
        self.client.force_login(self.coord)
        response = self.client.get(self.url(self.da_ana_com_tec1))
        self.assertContains(response, "(atrasado)")

    def test_link_de_volta_depende_do_papel(self):
        casos = {
            self.ana: reverse("tickets:list"),
            self.coord: reverse("accounts:home"),
        }
        for user, destino in casos.items():
            with self.subTest(papel=user.role):
                self.client.force_login(user)
                response = self.client.get(self.url(self.da_ana_com_tec1))
                self.assertContains(response, f'href="{destino}"')
