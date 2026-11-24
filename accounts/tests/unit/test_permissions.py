from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from django.views import View

from accounts.models import User
from accounts.permissions import RoleRequiredMixin, has_role, role_required

Role = User.Role


@role_required(Role.COORDENADOR, Role.TECNICO)
def equipe_ti(request):
    """View de exemplo restrita a coordenador e técnico."""
    return HttpResponse("ok")


class SomenteCoordenador(RoleRequiredMixin, View):
    allowed_roles = (Role.COORDENADOR,)

    def get(self, request):
        return HttpResponse("ok")


class SemPapeis(RoleRequiredMixin, View):
    def get(self, request):
        return HttpResponse("ok")


def requisicao(user, path="/restrita/?aba=1"):
    request = RequestFactory().get(path)
    request.user = user
    return request


class HasRoleTests(SimpleTestCase):
    def test_anonimo_nunca_tem_papel(self):
        self.assertFalse(has_role(AnonymousUser(), *Role.values))

    def test_confere_se_o_papel_esta_entre_os_informados(self):
        user = User(role=Role.TECNICO)
        self.assertTrue(has_role(user, Role.COORDENADOR, Role.TECNICO))
        self.assertFalse(has_role(user, Role.SOLICITANTE))


class RoleRequiredDecoratorTests(SimpleTestCase):
    def test_anonimo_vai_para_o_login_com_next(self):
        response = equipe_ti(requisicao(AnonymousUser()))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/entrar/?next=/restrita/%3Faba%3D1")

    def test_papel_fora_da_lista_recebe_acesso_negado(self):
        with self.assertRaises(PermissionDenied):
            equipe_ti(requisicao(User(role=Role.SOLICITANTE)))

    def test_qualquer_papel_da_lista_passa(self):
        for papel in (Role.COORDENADOR, Role.TECNICO):
            with self.subTest(papel=papel):
                response = equipe_ti(requisicao(User(role=papel)))
                self.assertEqual(response.status_code, 200)

    def test_preserva_o_nome_da_view(self):
        self.assertEqual(equipe_ti.__name__, "equipe_ti")

    def test_recusa_configuracao_sem_papel_ou_com_papel_desconhecido(self):
        for papeis in ((), ("TECNICOS",)):
            with self.subTest(papeis=papeis), self.assertRaises(ValueError):
                role_required(*papeis)


class RoleRequiredMixinTests(SimpleTestCase):
    def test_anonimo_vai_para_o_login_com_next(self):
        response = SomenteCoordenador.as_view()(requisicao(AnonymousUser()))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/entrar/?next=/restrita/%3Faba%3D1")

    def test_papel_errado_recebe_acesso_negado(self):
        for papel in (Role.SOLICITANTE, Role.TECNICO):
            with self.subTest(papel=papel), self.assertRaises(PermissionDenied):
                SomenteCoordenador.as_view()(requisicao(User(role=papel)))

    def test_papel_certo_passa(self):
        response = SomenteCoordenador.as_view()(requisicao(User(role=Role.COORDENADOR)))
        self.assertEqual(response.status_code, 200)

    def test_view_sem_allowed_roles_e_erro_de_configuracao(self):
        with self.assertRaises(ImproperlyConfigured):
            SemPapeis.as_view()(requisicao(User(role=Role.COORDENADOR)))
