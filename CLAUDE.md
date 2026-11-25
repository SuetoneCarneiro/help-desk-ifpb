# CLAUDE.md — Help Desk IFPB

Instruções para o assistente de IA (Claude Code) neste repositório. Versionado de propósito: a especificação do trabalho (seção 13) exige que a configuração do assistente fique no repositório.

## O projeto

Help Desk IFPB: chamados de TI de alunos e professores do campus João Pessoa, conduzidos como ordens de serviço (aberto → atribuído → em andamento → concluído; saídas: cancelado pelo solicitante, recusado pelo coordenador).

- Papéis: `SOLICITANTE`, `COORDENADOR`, `TECNICO` (campo `accounts.User.role`).
- Trabalho final de RAD; entrega e apresentação em **09/12/2026**.
- Quadro de tarefas: https://trello.com/b/BTALfjm8/projeto-rad-ifdesk — cards `SU*` (back-end, Suetone), `PA*` (front-end, Pedro Arthur), `PL*` (infra/testes, Pedro Lucas), `TEAM*`.
- Proposta e histórias de usuário: ver `docs/` e o README.

### As três recusas oficiais (precisam de teste do caminho feliz e do recusado)

1. **US4** — atribuição recusada quando o técnico já tem 5 ordens atribuídas ou em andamento.
2. **US9** — só o técnico designado pode iniciar o atendimento.
3. **US10** — conclusão recusada com descrição com menos de 20 caracteres.

## Stack e decisões

- Django 5.2 + Python 3.13, gerenciado **só com uv** (`pyproject.toml` + `uv.lock`; nunca `pip install` nem `requirements.txt` manual).
- Front-end em **templates Django** (decidido em 24/11). Sem SPA/CORS.
- SQLite (`SQLITE_PATH` no compose; volume `helpdesk-ifpb-dados`).
- Apps: `accounts` (usuário customizado, `AUTH_USER_MODEL = "accounts.User"`), `tickets` (`Location`, `Category`, `Ticket`). Modelagem em `docs/modelagem-banco.md`.
- Identificadores em inglês; textos para o usuário (`verbose_name`, mensagens) em português.
- **Regras de negócio e transições de status ficam em `tickets/services.py`**, nunca só na view ou no template — a mesma regra precisa valer para qualquer porta de entrada. As views só traduzem a exceção em mensagem.
- **Quem pode** (autorização) fica em `tickets/policies.py` (`can_*`, `ensure`); **quando pode** (regra de negócio) fica em `tickets/services.py`. Listas e detalhes de chamado partem de `Ticket.objects.visible_to(user)`. A matriz de permissões está em `docs/plano-su03-permissoes.md`.
- Cada serviço segue a ordem: `ensure(can_...)` (recusa → `PermissionDenied`, 403) → regra de negócio (recusa → `services.TicketRuleError`, que a view mostra com `form.add_error(None, ...)` ou `messages`) → grava. Modelo: `open_ticket` (SU04).
- Constantes de status para as regras: `Ticket.ACTIVE_STATUSES`, `Ticket.TECHNICIAN_LOAD_STATUSES`, `Ticket.CANCELLABLE_STATUSES`.

## Comandos

```bash
uv sync                                   # dependências
uv run manage.py runserver                # servidor local
uv run manage.py makemigrations           # depois de alterar model (commitar a migration junto)
uv run manage.py test --shuffle           # testes (runner do Django; nada de pytest)
uv run coverage run manage.py test --shuffle && uv run coverage report   # cobertura (mínimo 95%)
uv run pre-commit run --all-files         # esteira completa
docker compose up --build                 # sistema em http://localhost:8000
```

## Testes

- Cada app tem `tests/unit/` (peça isolada: model, função, form) e `tests/integration/` (requisição pelo test Client passando por URL, view, model e banco).
- Testes de autorização conferem a resposta **e** o estado do banco.
- A suíte precisa passar com `--shuffle`; nenhum teste usa o banco de desenvolvimento nem é marcado para pular.
- Código novo entra com teste no mesmo PR — a cobertura abaixo de 95% deixa o CI vermelho.

## Commits e PRs

- Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `build:`, `ci:`, `chore:`, `refactor:` …), em português, citando o card: `feat: modelos de chamado e usuário com papel (SU01)`.
- Commits **assinados** (SSH) e feitos pelo próprio integrante. O assistente não commita em nome de ninguém.
- Trabalhar em branch e abrir PR para `main`.

## Registro do uso de IA

- Prompts que geraram algo que ficou no sistema → entrada em `PROMPTS.md` (data, integrante, objetivo, prompt, **Resultado**).
- Planos, specs e quebras de tarefa gerados pela IA → `docs/`.
- Nunca colocar token, senha ou chave de API nestes arquivos.
