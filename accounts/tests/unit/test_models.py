from django.test import SimpleTestCase

from accounts.models import User


class UserRoleTests(SimpleTestCase):
    def test_papel_padrao_e_solicitante(self):
        self.assertEqual(User().role, User.Role.SOLICITANTE)

    def test_propriedades_refletem_apenas_o_proprio_papel(self):
        casos = {
            User.Role.SOLICITANTE: (True, False, False),
            User.Role.COORDENADOR: (False, True, False),
            User.Role.TECNICO: (False, False, True),
        }
        for papel, esperado in casos.items():
            with self.subTest(papel=papel):
                user = User(role=papel)
                self.assertEqual(
                    (user.is_solicitante, user.is_coordenador, user.is_tecnico),
                    esperado,
                )
