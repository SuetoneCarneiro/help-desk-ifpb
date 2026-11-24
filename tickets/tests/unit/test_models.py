from datetime import timedelta

from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from accounts.models import User
from tickets.models import Category, Location, Ticket

S = Ticket.Status


class TicketBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.solicitante = User.objects.create_user("aluno", role=User.Role.SOLICITANTE)
        cls.tecnico = User.objects.create_user("tecnico", role=User.Role.TECNICO)
        cls.local = Location.objects.create(name="Bloco A - Lab 1")
        cls.tipo = Category.objects.create(name="Computador")

    def make(self, **extra):
        campos = {
            "requester": self.solicitante,
            "location": self.local,
            "category": self.tipo,
            "description": "Computador não liga",
        }
        if extra.get("status") in (S.ATRIBUIDO, S.EM_ANDAMENTO, S.CONCLUIDO):
            campos |= {"technician": self.tecnico, "priority": Ticket.Priority.MEDIA}
        return Ticket.objects.create(**(campos | extra))


class StrTests(TicketBase):
    def test_str_de_local_e_tipo_e_o_nome(self):
        self.assertEqual(str(self.local), "Bloco A - Lab 1")
        self.assertEqual(str(self.tipo), "Computador")

    def test_str_do_chamado_mostra_numero_tipo_e_local(self):
        ticket = self.make()
        self.assertEqual(str(ticket), f"#{ticket.pk} — Computador em Bloco A - Lab 1")


class TicketDefaultsTests(TicketBase):
    def test_chamado_novo_nasce_aberto_sem_tecnico_prioridade_e_prazo(self):
        ticket = self.make()
        self.assertEqual(ticket.status, S.ABERTO)
        self.assertIsNone(ticket.technician)
        self.assertIsNone(ticket.priority)
        self.assertIsNone(ticket.due_at)
        self.assertIsNotNone(ticket.created_at)


class TicketConstraintTests(TicketBase):
    def test_chamado_em_atendimento_sem_tecnico_e_recusado_pelo_banco(self):
        with self.assertRaises(IntegrityError):
            self.make(status=S.ATRIBUIDO, technician=None)

    def test_chamado_em_atendimento_sem_prioridade_e_recusado_pelo_banco(self):
        with self.assertRaises(IntegrityError):
            self.make(status=S.EM_ANDAMENTO, priority=None)

    def test_nao_apaga_local_com_chamados(self):
        self.make()
        with self.assertRaises(ProtectedError):
            self.local.delete()


class TicketQuerySetTests(TicketBase):
    def setUp(self):
        self.agora = timezone.now()
        self.por_status = {status: self.make(status=status) for status in S.values}

    def ids(self, queryset):
        return set(queryset.values_list("status", flat=True))

    def test_active_inclui_aberto_atribuido_e_em_andamento(self):
        self.assertEqual(
            self.ids(Ticket.objects.active()),
            {S.ABERTO, S.ATRIBUIDO, S.EM_ANDAMENTO},
        )

    def test_technician_load_inclui_atribuido_e_em_andamento(self):
        self.assertEqual(
            self.ids(Ticket.objects.technician_load()),
            {S.ATRIBUIDO, S.EM_ANDAMENTO},
        )

    def test_overdue_traz_so_ordens_em_atendimento_com_prazo_vencido(self):
        vencido = self.agora - timedelta(hours=1)
        Ticket.objects.filter(status__in=[S.EM_ANDAMENTO, S.CONCLUIDO]).update(
            due_at=vencido
        )
        Ticket.objects.filter(status=S.ATRIBUIDO).update(
            due_at=self.agora + timedelta(hours=1)
        )

        self.assertEqual(
            self.ids(Ticket.objects.overdue(now=self.agora)), {S.EM_ANDAMENTO}
        )

    def test_overdue_sem_data_usa_o_horario_atual(self):
        Ticket.objects.filter(status=S.ATRIBUIDO).update(
            due_at=self.agora - timedelta(days=1)
        )
        self.assertEqual(self.ids(Ticket.objects.overdue()), {S.ATRIBUIDO})


class TicketDeadlineTests(SimpleTestCase):
    def test_prazo_por_prioridade(self):
        inicio = timezone.now()
        casos = {
            Ticket.Priority.URGENTE: timedelta(hours=4),
            Ticket.Priority.ALTA: timedelta(hours=24),
            Ticket.Priority.MEDIA: timedelta(hours=72),
            Ticket.Priority.BAIXA: timedelta(hours=120),
        }
        for prioridade, prazo in casos.items():
            with self.subTest(prioridade=prioridade):
                self.assertEqual(
                    Ticket.deadline_for(prioridade, inicio), inicio + prazo
                )

    def test_prioridade_inexistente_e_recusada(self):
        with self.assertRaises(ValueError):
            Ticket.deadline_for(99, timezone.now())


class TicketIsOverdueTests(SimpleTestCase):
    def setUp(self):
        self.agora = timezone.now()
        self.passado = self.agora - timedelta(minutes=1)

    def test_em_atendimento_com_prazo_vencido_esta_atrasado(self):
        for status in (S.ATRIBUIDO, S.EM_ANDAMENTO):
            with self.subTest(status=status):
                ticket = Ticket(status=status, due_at=self.passado)
                self.assertTrue(ticket.is_overdue(now=self.agora))

    def test_dentro_do_prazo_nao_esta_atrasado(self):
        ticket = Ticket(status=S.ATRIBUIDO, due_at=self.agora + timedelta(minutes=1))
        self.assertFalse(ticket.is_overdue(now=self.agora))
        self.assertFalse(ticket.is_overdue())

    def test_sem_prazo_ou_fora_de_atendimento_nao_esta_atrasado(self):
        casos = [
            Ticket(status=S.ATRIBUIDO, due_at=None),
            Ticket(status=S.ABERTO, due_at=self.passado),
            Ticket(status=S.CONCLUIDO, due_at=self.passado),
        ]
        for ticket in casos:
            with self.subTest(status=ticket.status):
                self.assertFalse(ticket.is_overdue(now=self.agora))
