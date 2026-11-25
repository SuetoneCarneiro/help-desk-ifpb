# Plano — SU04: abertura de chamados (US1)

> Gerado com apoio de IA (Claude Code) em 25/11/2026 para o card [SU04](https://trello.com/c/pD1GuU9c). Revisar antes de implementar.
> Depende de: SU01 (`Ticket`, `ACTIVE_STATUSES`), SU02 (`role_required`, login) e SU03 (`can_open_ticket`, `ensure`), todos na `main`.
> Par no front-end: **PA04** (Pedro Arthur), formulário de abertura.

## O que o card pede

| Critério | Como fica |
| --- | --- |
| Solicitante abre chamado com local, tipo de equipamento e descrição | Formulário em `/chamados/novo/` → serviço `open_ticket(...)` |
| Chamado associado ao usuário autenticado | O serviço usa `request.user`; o formulário **não tem** campo de solicitante |
| Status inicial `ABERTO` e data de abertura | Padrão do model (`status`) e `created_at` (`auto_now_add`) |
| Recusa sem local ou descrição | Formulário (campo obrigatório) **e** serviço (descrição só com espaços) |
| Recusa com 3 chamados ativos | Serviço conta `requester.requested_tickets.active()`; ativos = `Ticket.ACTIVE_STATUSES` |

## Primeiro `services.py`: o padrão para os próximos cards

Este é o primeiro card com regra de negócio, então ele define como as próximas regras (de SU06 até SU13) vão ser escritas.

```python
# tickets/services.py (resumo; o código completo está no arquivo)
class TicketRuleError(Exception):
    """Uma regra de negócio recusou a operação. A mensagem vai para o usuário."""


def open_ticket(*, requester, location, category, description) -> Ticket:
    ensure(can_open_ticket(requester))  # QUEM: policies.py → 403
    if not description.strip():
        raise TicketRuleError("...")  # QUANDO: regra → mensagem no form
    active = requester.requested_tickets.active().count()
    if active >= Ticket.MAX_ACTIVE_PER_REQUESTER:
        raise TicketRuleError("Você já tem 3 chamados ativos...")
    return Ticket.objects.create(...)
```

| Tipo de recusa | Exceção | A view faz | Resposta |
| --- | --- | --- | --- |
| Papel ou dono errado (**quem**) | `PermissionDenied` (via `ensure`) | nada: o Django responde | 403 |
| Regra de negócio (**quando**) | `TicketRuleError` | `form.add_error(None, str(erro))` | 200 com a mensagem no form |
| Campo faltando ou inválido | validação do form | re-renderiza o form | 200 com o erro no campo |

### Explicação simples

> **A view só cuida da tela; quem decide se o chamado pode ser aberto é o serviço.** A view recebe o formulário, chama `open_ticket(...)` e, se o serviço disser "não", mostra a mensagem dele.

Por que não deixar a regra na view? Porque a view é só **uma** das portas de entrada. Pelo admin, pelo shell ou por uma API, a regra dos 3 chamados precisa valer igual. Com a regra no serviço, ela vale para todas as portas, e o teste unitário do serviço prova isso sem precisar de tela.

## Arquivos

```
tickets/services.py                   TicketRuleError, open_ticket
tickets/models.py                     Ticket.MAX_ACTIVE_PER_REQUESTER = 3
tickets/forms.py                      TicketOpenForm (ModelForm: location, category, description)
tickets/views.py                      ticket_create (role_required(SOLICITANTE))
tickets/urls.py                       app_name = "tickets"; "chamados/novo/" → name="create"
tickets/templates/tickets/ticket_form.html   mínimo, sem estilo (PA04 estiliza)
templates/base.html                   bloco de mensagens (django.contrib.messages)
accounts/templates/accounts/home.html link "Abrir chamado" para o solicitante
config/urls.py                        include("tickets.urls")
```

## Comportamento esperado

| Situação | Resposta | Banco |
| --- | --- | --- |
| Solicitante envia dados válidos | 302 para o painel, com a mensagem "Chamado #N aberto." | +1 chamado `ABERTO`, solicitante = quem está logado |
| POST tenta mandar `requester=<outro id>` | ignorado (o campo não existe no form) | chamado continua sendo de quem está logado |
| Falta local, tipo ou descrição | 200 com o erro no campo | nada criado |
| Descrição só com espaços | 200 com o erro no campo (o form já remove os espaços) | nada criado |
| Já tem 3 ativos (aberto, atribuído ou em andamento) | 200 com a mensagem do limite | nada criado |
| Tem 3 chamados, mas um concluído, cancelado ou recusado | abre normalmente | +1 |
| Coordenador ou técnico | 403 | nada criado |
| Anônimo | 302 para o login | nada criado |

## Testes

- **Unitários** (`tickets/tests/unit/test_services.py`): caminho feliz; limite com 3 ativos; status que não contam (concluído, cancelado, recusado); chamados de **outro** solicitante não contam; descrição vazia ou só com espaços; papel errado levanta `PermissionDenied`. Em toda recusa, conferir que o número de chamados não mudou.
- **Unitários** (`tickets/tests/unit/test_forms.py`): campos obrigatórios; o form não expõe `requester` nem `status`.
- **Integração** (`tickets/tests/integration/test_open_ticket.py`): GET do form; POST válido; POST sem local; POST no limite; `requester` forjado no POST; coordenador ou técnico 403; anônimo vai para o login. Toda recusa confere a resposta **e** o banco.

## Pontos de atenção

- **Concorrência**: dois envios ao mesmo tempo com 2 ativos poderiam abrir o 4º. O serviço roda em `transaction.atomic()` e trava a linha do solicitante (`select_for_update`). No SQLite o banco já serializa as escritas, e no PostgreSQL a trava garante. É um caso raro, mas fácil de explicar.
- **Seed (PL17)**: sem locais e tipos de equipamento cadastrados, o formulário fica com as listas vazias. Os testes criam os próprios dados. Para testar à mão, cadastre pelo `/admin` até o seed existir.
- **PA04**: contrato do template — `form` (campos `location`, `category`, `description`, `form.non_field_errors` para a mensagem do limite) e `messages` para a confirmação.
- **Depois do envio**: vai para o painel porque a lista "meus chamados" é a SU05. Quando ela existir, o redirecionamento passa a ser para o detalhe do chamado.
