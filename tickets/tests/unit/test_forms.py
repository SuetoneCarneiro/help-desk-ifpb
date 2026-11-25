from django.test import TestCase

from tickets.forms import TicketOpenForm
from tickets.tests.factories import criar_local_e_tipo


class TicketOpenFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.local, cls.tipo = criar_local_e_tipo()

    def test_expoe_so_local_tipo_e_descricao(self):
        self.assertEqual(
            list(TicketOpenForm().fields), ["location", "category", "description"]
        )

    def test_valido_com_os_tres_campos(self):
        form = TicketOpenForm(
            {
                "location": self.local.pk,
                "category": self.tipo.pk,
                "description": "Sem rede.",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_os_tres_campos_sao_obrigatorios(self):
        form = TicketOpenForm({"description": "   "})
        self.assertFalse(form.is_valid())
        self.assertEqual(set(form.errors), {"location", "category", "description"})

    def test_local_inexistente_e_recusado(self):
        form = TicketOpenForm(
            {"location": 999, "category": self.tipo.pk, "description": "Sem rede."}
        )
        self.assertIn("location", form.errors)
