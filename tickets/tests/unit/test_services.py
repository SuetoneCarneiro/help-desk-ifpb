from django.core.exceptions import PermissionDenied
from django.test import TestCase

from accounts.models import User
from tickets import services
from tickets.models import Ticket
from tickets.tests.factories import criar_chamado, criar_local_e_tipo, criar_usuario

Role = User.Role
Status = Ticket.Status


class OpenTicketTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = criar_usuario("ana")
        cls.bia = criar_usuario("bia")
        cls.tecnico = criar_usuario("tec", Role.TECNICO)
        cls.local, cls.tipo = criar_local_e_tipo()

    def abrir(self, requester=None, **dados):
        dados = {
            "location": self.local,
            "category": self.tipo,
            "description": "  Projetor não liga.  ",
            **dados,
        }
        return services.open_ticket(requester=requester or self.ana, **dados)

    def com_ativos(self, quantidade, requester=None, status=Status.ABERTO):
        for _ in range(quantidade):
            criar_chamado(
                requester or self.ana, self.local, self.tipo, status, self.tecnico
            )

    def test_abre_chamado_aberto_do_solicitante_com_data(self):
        ticket = self.abrir()
        ticket.refresh_from_db()
        self.assertEqual(ticket.requester, self.ana)
        self.assertEqual(ticket.status, Status.ABERTO)
        self.assertEqual(ticket.description, "Projetor não liga.")
        self.assertIsNotNone(ticket.created_at)
        self.assertIsNone(ticket.technician)

    def test_abre_com_dois_ativos(self):
        self.com_ativos(2)
        self.abrir()
        self.assertEqual(self.ana.requested_tickets.active().count(), 3)

    def test_recusa_o_quarto_chamado_ativo_sem_gravar(self):
        for status in Ticket.ACTIVE_STATUSES:
            with self.subTest(status=status):
                Ticket.objects.all().delete()
                self.com_ativos(2)
                self.com_ativos(1, status=status)
                with self.assertRaisesMessage(
                    services.TicketRuleError, "3 chamados ativos"
                ):
                    self.abrir()
                self.assertEqual(Ticket.objects.count(), 3)

    def test_chamados_encerrados_nao_contam_no_limite(self):
        for status in (Status.CONCLUIDO, Status.CANCELADO, Status.RECUSADO):
            self.com_ativos(1, status=status)
        self.com_ativos(2)
        self.abrir()
        self.assertEqual(Ticket.objects.filter(requester=self.ana).count(), 6)

    def test_chamados_de_outro_solicitante_nao_contam(self):
        self.com_ativos(3, requester=self.bia)
        self.abrir()
        self.assertEqual(self.ana.requested_tickets.count(), 1)

    def test_recusa_sem_local_tipo_ou_descricao_sem_gravar(self):
        faltando = {
            "sem local": {"location": None},
            "sem tipo": {"category": None},
            "descrição vazia": {"description": ""},
            "descrição só com espaços": {"description": "   \n "},
        }
        for caso, dados in faltando.items():
            with self.subTest(caso=caso):
                with self.assertRaises(services.TicketRuleError):
                    self.abrir(**dados)
                self.assertFalse(Ticket.objects.exists())

    def test_quem_nao_e_solicitante_recebe_acesso_negado_sem_gravar(self):
        for papel in (Role.COORDENADOR, Role.TECNICO):
            with self.subTest(papel=papel):
                user = criar_usuario(f"u-{papel.lower()}", papel)
                with self.assertRaises(PermissionDenied):
                    self.abrir(requester=user)
                self.assertFalse(Ticket.objects.exists())
