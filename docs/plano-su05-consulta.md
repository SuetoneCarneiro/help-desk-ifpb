# Plano — SU05: consulta e acompanhamento dos próprios chamados (US2)

> Gerado com apoio de IA (Claude Code) em 27/11/2026 para o card [SU05](https://trello.com/c/OAjGCDVg). Revisar antes de implementar.
> Depende de: SU02 (login, `RoleRequiredMixin`), SU03 (`visible_to`, `can_view_ticket`) e SU04 (abertura), todos na `main`.
> Par no front-end: **PA05** (Pedro Arthur), listagem e acompanhamento.

## O que o card pede

| Critério | Como fica |
| --- | --- |
| Listar os chamados do usuário logado | `/chamados/` → `Ticket.objects.visible_to(user)` (para o solicitante, só os dele) |
| Mostrar nº, local, tipo, descrição, status, prioridade, abertura, técnico e prazo | Colunas da lista; o detalhe mostra tudo, inclusive motivo da recusa e solução |
| Consulta individual | `/chamados/<id>/` |
| Chamado de outra pessoa não aparece na lista | Vem de graça do `visible_to` |
| Acesso direto a chamado alheio é recusado | **404** (decisão da SU03: na consulta, não revelar que o chamado existe) |

## Decisões

| Decisão | Motivo |
| --- | --- |
| **Lista só para o solicitante** ("Meus chamados") | A consulta geral do coordenador é a SU09 (com filtros e atrasados), e as ordens do técnico são a SU11 (ordenadas por prioridade e prazo). Fazer uma lista para todos aqui invadiria esses cards. |
| **Detalhe para qualquer papel**, via `visible_to` | A mesma página serve ao solicitante (SU05), ao coordenador (SU09) e ao técnico (SU11). Cada um só abre o que enxerga; o resto dá 404. Os botões de ação (cancelar, iniciar, concluir) entram nesta página nos cards deles. |
| **Views em classe** (`ListView`, `DetailView`) | Primeiro uso do `RoleRequiredMixin` da SU02. O `DetailView` com `get_queryset() = visible_to(user)` já devolve 404 sozinho para chamado fora do conjunto, sem `if` na view. |
| **Paginação de 20** | Os chamados encerrados continuam na lista para sempre; sem paginação, a página cresce sem limite. |
| `select_related("location", "category", "technician")` | Sem isso, cada linha da lista faria 3 consultas a mais (o problema "N+1"). Um teste conta as consultas. |
| Depois de abrir um chamado → vai para o **detalhe** dele | Estava pendente desde a SU04 (ia para o painel porque o detalhe não existia). |

### Explicação simples

> **A lista e o detalhe não decidem quem vê o quê: os dois perguntam ao `visible_to`.** Se o chamado não está no conjunto do usuário, para ele o chamado "não existe" (404).

Por que 404 e não 403? Um 403 diria "esse chamado existe, mas não é seu". Trocando o número na URL, alguém descobriria quantos chamados o campus tem. O 404 não revela nada.

## Arquivos

```
tickets/views.py                            MyTicketListView (RoleRequiredMixin + ListView)
                                            TicketDetailView (LoginRequiredMixin + DetailView)
                                            ticket_create → redireciona para o detalhe
tickets/urls.py                             "chamados/" (tickets:list), "chamados/<int:pk>/" (tickets:detail)
tickets/templates/tickets/ticket_list.html  tabela mínima + paginação (PA05 estiliza)
tickets/templates/tickets/ticket_detail.html todos os campos; motivo da recusa e solução quando houver
accounts/templates/accounts/home.html       atalho "Meus chamados" para o solicitante
```

## Comportamento esperado

| Situação | Resposta |
| --- | --- |
| Solicitante abre `/chamados/` | 200 só com os chamados dele, do mais novo para o mais antigo |
| Solicitante sem chamados | 200 com "Você ainda não abriu nenhum chamado." e o atalho para abrir |
| Coordenador ou técnico abre `/chamados/` | 403 (a lista deles vem na SU09 e na SU11) |
| Solicitante abre o próprio chamado | 200 com todos os dados |
| Solicitante abre o chamado de outra pessoa | **404** |
| Coordenador abre qualquer chamado | 200 |
| Técnico abre chamado atribuído a ele / a outro técnico | 200 / **404** |
| Anônimo em qualquer uma | 302 para o login |
| Chamado recusado | o detalhe mostra o motivo (pedido também pela SU08) |
| Chamado concluído | o detalhe mostra a descrição do atendimento |

## Testes

- **Integração** (`tickets/tests/integration/test_consulta.py`): lista só com os próprios chamados (com chamados de outro solicitante no banco); ordem; lista vazia; paginação; lista 403 para coordenador e técnico; detalhe: dono 200, outro solicitante 404, coordenador 200, técnico designado 200, outro técnico 404, anônimo para o login; motivo da recusa e solução aparecem quando existem; número de consultas da lista não cresce com o número de chamados (`assertNumQueries`); abertura redireciona para o detalhe.
- O teste atual da SU04 que espera o redirecionamento para o painel passa a esperar o detalhe.

## Pontos de atenção

- **PA05**: contrato dos templates — lista: `page_obj` / `ticket_list` com os campos do model e `get_status_display` / `get_priority_display`; detalhe: `ticket`. O `is_overdue` já existe no model para o indicador de atraso.
- **Prazo e prioridade** só existem depois da atribuição (SU07); até lá aparecem como "—".
- **Página de 404**: com `DEBUG=True` (o padrão do compose), o Django mostra a própria página técnica de 404. Ela é igual para um chamado alheio e para um inexistente, então não vaza nada. Uma `templates/404.html` em português só aparece com `DEBUG=False`; fica como melhoria opcional.
- **Risco de cronograma**: faltam 12 dias para 09/12 e ainda não há commits do front-end (PA*). As telas mínimas do back-end permitem demonstrar tudo, mas vale combinar com o Pedro Arthur o que ele assume a partir delas.
