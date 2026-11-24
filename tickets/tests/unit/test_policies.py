"""Matriz papel × operação da SU03 (docs/plano-su03-permissoes.md)."""

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import SimpleTestCase, TestCase

from accounts.models import User
from tickets import policies
from tickets.models import Category, Location, Ticket

Role = User.Role

# Atores fixos, sem banco: as políticas só comparam papel e ids.
DONO = User(pk=1, username="dono", role=Role.SOLICITANTE)
OUTRO_SOLICITANTE = User(pk=2, username="outro", role=Role.SOLICITANTE)
COORDENADOR = User(pk=3, username="coord", role=Role.COORDENADOR)
TECNICO_DESIGNADO = User(pk=4, username="tec", role=Role.TECNICO)
OUTRO_TECNICO = User(pk=5, username="tec2", role=Role.TECNICO)
ANONIMO = AnonymousUser()

ATORES = {
    "dono": DONO,
    "outro solicitante": OUTRO_SOLICITANTE,
    "coordenador": COORDENADOR,
    "técnico designado": TECNICO_DESIGNADO,
    "outro técnico": OUTRO_TECNICO,
    "anônimo": ANONIMO,
}


# Operação → papéis que podem.
MATRIZ_POR_PAPEL = {
    policies.can_open_ticket: {Role.SOLICITANTE},
    policies.can_assign_ticket: {Role.COORDENADOR},
    policies.can_refuse_ticket: {Role.COORDENADOR},
    policies.can_view_all_tickets: {Role.COORDENADOR},
    policies.can_view_reports: {Role.COORDENADOR},
}

# Operação → atores que podem, num chamado do DONO atribuído ao TECNICO_DESIGNADO.
MATRIZ_POR_CHAMADO = {
    policies.can_view_ticket: {"dono", "coordenador", "técnico designado"},
    policies.can_cancel_ticket: {"dono"},
    policies.can_start_ticket: {"técnico designado"},
    policies.can_complete_ticket: {"técnico designado"},
}


class EnsureTests(SimpleTestCase):
    def test_sim_passa_sem_erro(self):
        policies.ensure(True)

    def test_nao_vira_acesso_negado_com_mensagem(self):
        with self.assertRaisesMessage(PermissionDenied, "Só o técnico designado."):
            policies.ensure(False, "Só o técnico designado.")


class PoliticasPorPapelTests(SimpleTestCase):
    """Operações que dependem só do papel."""

    def test_cada_operacao_libera_so_os_papeis_da_matriz(self):
        for politica, papeis in MATRIZ_POR_PAPEL.items():
            for papel in Role.values:
                with self.subTest(operacao=politica.__name__, papel=papel):
                    self.assertEqual(politica(User(role=papel)), papel in papeis)

    def test_anonimo_nao_pode_nenhuma_operacao(self):
        for politica in MATRIZ_POR_PAPEL:
            with self.subTest(operacao=politica.__name__):
                self.assertFalse(politica(ANONIMO))


class PoliticasPorChamadoTests(SimpleTestCase):
    """Operações que dependem do papel e do chamado."""

    def setUp(self):
        self.chamado = Ticket(requester_id=DONO.pk, technician_id=TECNICO_DESIGNADO.pk)

    def test_cada_operacao_libera_so_os_atores_da_matriz(self):
        for politica, permitidos in MATRIZ_POR_CHAMADO.items():
            for nome, ator in ATORES.items():
                with self.subTest(operacao=politica.__name__, ator=nome):
                    self.assertEqual(politica(ator, self.chamado), nome in permitidos)

    def test_chamado_sem_tecnico_nao_pode_ser_iniciado_nem_concluido(self):
        chamado = Ticket(requester_id=DONO.pk, technician_id=None)
        for politica in (policies.can_start_ticket, policies.can_complete_ticket):
            for nome in ("técnico designado", "outro técnico"):
                with self.subTest(operacao=politica.__name__, ator=nome):
                    self.assertFalse(politica(ATORES[nome], chamado))


class VisibleToTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        criar = User.objects.create_user
        cls.ana = criar("ana", role=Role.SOLICITANTE)
        cls.bia = criar("bia", role=Role.SOLICITANTE)
        cls.coord = criar("coord", role=Role.COORDENADOR)
        cls.tec1 = criar("tec1", role=Role.TECNICO)
        cls.tec2 = criar("tec2", role=Role.TECNICO)
        local = Location.objects.create(name="Lab 1")
        tipo = Category.objects.create(name="Computador")

        def chamado(requester, technician=None):
            extra = {}
            if technician:
                extra = {
                    "technician": technician,
                    "status": Ticket.Status.ATRIBUIDO,
                    "priority": Ticket.Priority.MEDIA,
                }
            return Ticket.objects.create(
                requester=requester,
                location=local,
                category=tipo,
                description="Não liga",
                **extra,
            )

        cls.ana_aberto = chamado(cls.ana)
        cls.ana_tec1 = chamado(cls.ana, cls.tec1)
        cls.bia_tec2 = chamado(cls.bia, cls.tec2)
        cls.todos = {cls.ana_aberto, cls.ana_tec1, cls.bia_tec2}

    def visiveis(self, user):
        return set(Ticket.objects.visible_to(user))

    def test_cada_papel_ve_exatamente_o_seu_conjunto(self):
        casos = {
            "ana (solicitante)": (self.ana, {self.ana_aberto, self.ana_tec1}),
            "bia (solicitante)": (self.bia, {self.bia_tec2}),
            "coordenador": (self.coord, self.todos),
            "tec1": (self.tec1, {self.ana_tec1}),
            "tec2": (self.tec2, {self.bia_tec2}),
        }
        for nome, (user, esperado) in casos.items():
            with self.subTest(usuario=nome):
                self.assertEqual(self.visiveis(user), esperado)

    def test_anonimo_e_papel_desconhecido_nao_veem_nada(self):
        for user in (AnonymousUser(), User(pk=999, role="DESCONHECIDO")):
            with self.subTest(user=user):
                self.assertEqual(self.visiveis(user), set())

    def test_lista_e_detalhe_concordam(self):
        """Ninguém vê na lista um chamado que não poderia abrir, e vice-versa."""
        for user in (
            self.ana,
            self.bia,
            self.coord,
            self.tec1,
            self.tec2,
            AnonymousUser(),
        ):
            visiveis = self.visiveis(user)
            for ticket in self.todos:
                with self.subTest(user=str(user), chamado=ticket.pk):
                    self.assertEqual(
                        policies.can_view_ticket(user, ticket), ticket in visiveis
                    )
