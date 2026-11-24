# Plano — SU03: controle de acesso e permissões por papel

> Gerado com apoio de IA (Claude Code) em 24/11/2026 para o card [SU03](https://trello.com/c/v7P1vq9d). Revisar antes de implementar.
> Depende de: SU01 (`Ticket`, `User.role`) e SU02 (`role_required`, `RoleRequiredMixin`, página 403), ambos na `main`.

## Explicação simples da decisão

> **O `policies.py` é o lugar único onde está escrito quem pode fazer o quê no sistema.** Todas as telas e serviços consultam esse arquivo, em vez de cada um decidir por conta própria.

**Analogia.** Num prédio com vários setores, cada porteiro poderia ter a sua própria lista de quem pode entrar. Quando uma regra muda, alguém precisa avisar todos os porteiros, e um deles vai ficar com a lista desatualizada. No Help Desk existe **uma lista só**, e todo porteiro (cada tela e cada serviço) consulta a mesma.

**Como funciona.** Cada função responde uma pergunta de sim ou não, por exemplo: *"este usuário pode cancelar este chamado?"* (`can_cancel_ticket(user, ticket)`). Os testes percorrem a tabela inteira de papéis × operações, então qualquer mudança errada numa regra aparece na hora.

**Quem × quando.**

| O arquivo responde | Exemplo |
| --- | --- |
| `policies.py` → **quem** pode | "Só o técnico designado inicia o atendimento" |
| `services.py` → **quando** pode | "Só conclui se a descrição tiver 20 caracteres" |

**Respostas curtas para a apresentação.**

- *"Por que não esconder o botão e pronto?"* Esconder o botão é só aparência: quem conhece a URL ainda consegue mandar a requisição. A verificação precisa estar no servidor.
- *"Por que não usar os grupos e permissões do Django?"* O Django não tem pronto o "só o dono" ou "só o designado", que é permissão por chamado. Para três papéis fixos, umas poucas funções são mais simples de ler e testar.
- *"Como sabem que está certo?"* Os testes cobrem cada papel contra cada operação, incluindo dono e não dono e o técnico designado e outro técnico. Um teste também garante que a **lista** (`visible_to`) e o **detalhe** (`can_view_ticket`) nunca discordem.

**Vantagens e custos (resumo).**

| Ganha | Paga |
| --- | --- |
| Regra num lugar só, sem cópias divergentes | Os critérios do card (403 e banco inalterado pela requisição) só ficam provados de ponta a ponta quando as views chegarem (SU04 a SU13) |
| Vale para tela, admin, shell e API | Duas camadas para lembrar: `role_required` na view e `ensure(...)` no serviço |
| Evita ver chamado alheio trocando o número na URL (`visible_to`) | Algumas funções são simples ("é coordenador?") e foram escritas antes de quem vai usá-las |
| Testes rápidos, sem banco, em forma de tabela | Mais um conceito que os três integrantes precisam saber explicar |

## O problema de escopo

O card pede para proteger "views, permissões e endpoints" de abrir, consultar, cancelar, atribuir, recusar, iniciar e concluir. **Nenhuma dessas views existe ainda**: cada uma nasce num card próprio, de SU04 até SU13. Se a SU03 criasse as views, ela engoliria esses cards. Se esperasse por eles, ficaria para o fim e cada card reinventaria a checagem.

**Proposta:** a SU03 entrega a **regra de quem pode o quê** num lugar só, testada como uma matriz papel × operação. Cada card seguinte só **usa** essa regra na view ou no serviço e testa a requisição de ponta a ponta.

## Duas perguntas diferentes

| Pergunta | Exemplo | Onde fica | Card |
| --- | --- | --- | --- |
| **Quem** pode? (autorização) | "Só o dono cancela", "só o técnico designado inicia" | `tickets/policies.py` (SU03) | SU03 |
| **Quando** pode? (regra de negócio) | "Só cancela se aberto ou atribuído", "descrição ≥ 20 caracteres" | `tickets/services.py` | de SU04 até SU13 |

O serviço chama a política **antes** de aplicar a regra. A recusa de autorização vale para qualquer porta de entrada (tela, admin, shell, eventual API), como pede o CLAUDE.md.

## Matriz de permissões

| Operação | Solicitante | Coordenador | Técnico | Função |
| --- | --- | --- | --- | --- |
| Abrir chamado (US1) | ✅ | ❌ | ❌ | `can_open_ticket(user)` |
| Ver um chamado | só os próprios | todos | só os atribuídos a ele | `can_view_ticket(user, ticket)` |
| Listar chamados | só os próprios | todos | só os atribuídos a ele | `Ticket.objects.visible_to(user)` |
| Cancelar (US3) | só os próprios | ❌ | ❌ | `can_cancel_ticket(user, ticket)` |
| Atribuir técnico e prioridade (US4) | ❌ | ✅ | ❌ | `can_assign_ticket(user)` |
| Recusar (US5) | ❌ | ✅ | ❌ | `can_refuse_ticket(user)` |
| Consulta geral e atrasados (US6) | ❌ | ✅ | ❌ | `can_view_all_tickets(user)` |
| Relatório de produtividade (US7) | ❌ | ✅ | ❌ | `can_view_reports(user)` |
| Iniciar atendimento (US9, **Recusa 2**) | ❌ | ❌ | só o designado | `can_start_ticket(user, ticket)` |
| Concluir (US10) | ❌ | ❌ | só o designado | `can_complete_ticket(user, ticket)` |

O anônimo recebe ❌ em tudo, e `visible_to` devolve um queryset vazio para ele.

## Arquivos

```
tickets/policies.py                    funções can_* (puras: recebem user e ticket, devolvem bool)
                                       + ensure(allowed, message) → levanta PermissionDenied
tickets/models.py                      TicketQuerySet.visible_to(user)
tickets/tests/unit/test_policies.py    a matriz acima (uma linha por papel/ator × operação, com subTest),
                                       visible_to para cada papel e a concordância lista × detalhe
docs/plano-su03-permissoes.md          este arquivo (a matriz é a referência para os próximos cards)
```

## Convenção para os cards seguintes

| Situação | O que o código faz | Resposta |
| --- | --- | --- |
| Papel não pode a operação (ex.: técnico tenta atribuir) | view com `role_required` / `RoleRequiredMixin` | 403 |
| Papel pode, mas não **esse** chamado (ex.: cancelar o de outra pessoa) | serviço chama `ensure(can_cancel_ticket(user, ticket))` → `PermissionDenied` | 403 |
| Chamado fora do que o usuário enxerga (detalhe de chamado alheio) | view busca com `get_object_or_404(Ticket.objects.visible_to(user), pk=pk)` | 404 |
| Autorizado, mas a regra de negócio recusa (status errado, limite de 5, descrição curta) | serviço levanta erro de regra; a view mostra a mensagem | 200 com mensagem, ou 302 de volta |

Em todos os casos de recusa, o teste de integração do card confere a resposta **e** que o banco não mudou.

> **Decisão adotada (revisável na SU05) — 404 ou 403 para chamado de outra pessoa.** O 404 não revela que o chamado existe (padrão de segurança). O 403 segue a letra do card ("resposta de acesso negado"). Ficou assim: 404 na **consulta** (SU05) e 403 nas **operações** (cancelar, iniciar, concluir), porque ali o usuário já viu o chamado na própria lista. A SU03 não cria views, então a decisão só passa a valer no código a partir da SU05.

## Testes

- **Matriz** (`SimpleTestCase`, sem banco): cada linha da tabela vira um caso, cobrindo os três papéis e o anônimo. Para as operações de objeto há dois casos a mais: dono/designado ✅ e não dono/outro técnico ❌.
- **`visible_to`** (`TestCase`): com chamados de dois solicitantes e dois técnicos, cada papel vê exatamente o conjunto esperado.
- **`ensure`**: verdadeiro passa e falso levanta `PermissionDenied`.
- **Lista × detalhe**: para todo usuário e todo chamado, `can_view_ticket` é verdadeiro **se e somente se** o chamado está em `visible_to`.
- Os testes de integração (requisição → 403/404 → banco inalterado) entram em cada card, de SU04 até SU13, junto com a view.

## Fora do escopo

Views, formulários, templates e serviços de transição: são os cards de SU04 até SU13.
