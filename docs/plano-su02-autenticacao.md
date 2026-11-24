# Plano — SU02: autenticação e identificação dos papéis

> Gerado com apoio de IA (Claude Code) em 24/11/2026 para o card [SU02](https://trello.com/c/Hevy75Qq). Revisar antes de implementar.
> Depende de: SU01 (campo `User.role`, já na `main`). Destrava: SU03 (permissões por papel) e PA02 (tela de login).

## Escopo

| Item do card | Como fica |
| --- | --- |
| Usar a autenticação do Django | `LoginView` / `LogoutView` de `django.contrib.auth.views`, sessão do Django. |
| Configurar os três papéis | Já feito no SU01 (`User.Role`). |
| Identificar o papel do usuário autenticado | `request.user.role` e as propriedades `is_solicitante`, `is_coordenador` e `is_tecnico`; no template, `user.get_role_display`. |
| Login e logout | `accounts/urls.py`: `entrar/`, `sair/` (logout **só por POST**, como exige o Django 5) e o painel na raiz `/`. |
| Permissões reutilizáveis por papel | `accounts/permissions.py`: decorator `role_required(*roles)` e mixin `RoleRequiredMixin`. |
| Não autenticado não acessa área restrita | Anônimo → redireciona para o login com `?next=`; autenticado com papel errado → **403**. |
| Autenticação para a API | **Fora do escopo**: o front é em templates Django (decisão de 24/11). Se a API DRF for criada, usa `SessionAuthentication`. |

## Arquivos

```
accounts/
  permissions.py          role_required, RoleRequiredMixin
  views.py                home: painel provisório que mostra o papel de quem entrou
  urls.py                 app_name = "accounts"
  templates/
    registration/login.html   mínimo, sem estilo (PA02 estiliza)
    accounts/home.html        painel provisório por papel
templates/base.html        layout base com o botão "Sair" (form POST); TEMPLATES["DIRS"]
templates/403.html         "Acesso negado" em português (o Django usa esse nome sozinho)
config/settings.py         LOGIN_URL, LOGIN_REDIRECT_URL, LOGOUT_REDIRECT_URL
config/urls.py             include("accounts.urls")
```

## Comportamento esperado

| Situação | Resposta |
| --- | --- |
| Login com credenciais válidas | 302 para `accounts:home` (ou para o `next`) |
| Login com senha errada | 200 com a mensagem de erro do form, sem sessão |
| Anônimo acessa `/` | 302 para `entrar/?next=/` |
| `GET sair/` | 405 (logout só por POST) |
| `POST sair/` | sessão encerrada, 302 para o login |
| Papel errado numa view com `role_required` | 403 com a página "Acesso negado", e **nada muda no banco** |
| `next` apontando para outro site | ignorado; vai para o painel (proteção do próprio `LoginView`) |

## Testes

- `accounts/tests/unit/test_permissions.py` (com `RequestFactory`): anônimo é redirecionado, papel errado gera `PermissionDenied` e papel certo passa. Testar o decorator e o mixin, aceitando um ou vários papéis.
- `accounts/tests/integration/test_auth.py` (com o test `Client`): login válido, inválido e de usuário inativo, `next` interno e externo, painel protegido, logout por GET e por POST, e o painel mostrando o papel certo para cada um dos três papéis (`subTest`).
- Rota restrita de verdade: como as views com papel só chegam na SU03, `accounts/tests/integration/urls.py` cria uma view **só de teste** (`role_required(COORDENADOR)`, que grava um `Location`). Ela prova o 403 **e** que o banco continua vazio, para o anônimo e para os papéis errados.

## Combinar com o time

- **Pedro Arthur (PA02)**: o back-end entrega a view, a URL e um `registration/login.html` mínimo. O contrato é o contexto `form` (com `form.non_field_errors`) e `next`. O PA02 só troca o HTML e o CSS.
- **Pedro Lucas (PL17)**: o seed precisa criar ao menos um usuário de cada papel para o login ser demonstrado. Superusuários criados com `createsuperuser` nascem como `SOLICITANTE` (é o padrão do campo).
- **Painéis por papel**: ainda não existem. O `home` fica como painel provisório e, nos cards seguintes, passa a redirecionar para a fila de cada papel.
