# Plano de desenvolvimento — Help Desk IFPB

> Plano gerado com apoio de IA (Claude Code) em 24/11/2026, a partir da especificação do trabalho final e da proposta entregue.
> Versionado em `docs/` conforme a seção 13 da especificação ("Planos e specs gerados por IA").

## 1. Situação em 24/11

Faltam **15 dias** para a apresentação (09/12, 14h40).

| Item da especificação | Situação |
| --- | --- |
| uv + `pyproject.toml` + `uv.lock` versionados | ✅ feito |
| `.pre-commit-config.yaml` (ruff, pip-audit, conventional, check, migrations, cobertura) | ✅ feito |
| Pipeline no GitHub (esteira + validação de mensagens de commit + cobertura publicada) | ✅ verde |
| `docker-compose.yml` + `.env.example` | ✅ feito (só Django + SQLite) |
| Commits assinados (Verified) | ✅ todos até agora |
| Apps Django, models, regras, testes | ❌ nada ainda |
| Dados iniciais automáticos no `docker compose up` | ❌ |
| `CLAUDE.md`, `.claude/`, `PROMPTS.md`, `docs/` | ❌ (este arquivo é o primeiro) |
| Commits de todos os integrantes | ⚠️ Pedro Arthur (`Pedr04rthur`) ainda sem commits |
| Proteção do ramo `main` | ⚠️ desligada (recomendado, não obrigatório) |

## 2. Pendências de infraestrutura antes do back-end

Em ordem de urgência:

1. ~~**Decidir o front-end**~~ — **decidido em 24/11: templates Django.** Sem SPA, sem CORS e sem serviço extra no compose; autenticação por sessão do Django. API DRF fica opcional — se for criada, as três recusas precisam ser testadas "pelas duas portas" (seção 8).
2. **Ambiente local de cada integrante** (sem isso o commit não passa pela esteira nem sai Verified):
   `uv` instalado, `uv sync`, `uv run pre-commit install --install-hooks`, assinatura SSH configurada e chave cadastrada no GitHub como *signing key*.
3. **Custom user model antes da primeira migration.** `AUTH_USER_MODEL` precisa existir antes do primeiro `migrate` de apps próprios; trocar depois é caro.
4. **Artefatos de IA**: `CLAUDE.md` (convenções + comandos da esteira), `PROMPTS.md` na raiz, `docs/` com os planos. Conferir que `.gitignore` não ignora `.claude/` (hoje não ignora).
5. **Seed automático**: comando de gerência (`seed`/`bootstrap`) chamado pelo `CMD` do Dockerfile depois do `migrate`, idempotente.
6. **Estrutura de testes**: `tests/unit/` e `tests/integration/` em cada app (separação exigida na seção 8).
7. **Proteção da `main`** exigindo PR + CI verde + commits assinados (fortalece a seção 9.4).

## 3. Fases e datas

| Período | Fase | Entregas |
| --- | --- | --- |
| 24–25/11 | Infra pendente | Itens 1–4 acima; primeiro commit de cada integrante |
| 25–27/11 | Modelagem | App `chamados` (e `contas`), models, migrations, admin, seed inicial |
| 27/11–02/12 | Regras + back-end | Serviços de transição de status (US1–US10), views/API, permissões por papel, testes unitários e de integração das 3 recusas |
| 01–05/12 | Front-end + relatórios | Telas por papel, fila com filtros (US4), painel de atrasados (US6), produtividade (US7) |
| 05–07/12 | Fechamento | Cobertura ≥ 95% com folga, README completo, teste em máquina limpa (`docker compose down -v`, `docker image prune`) |
| 08/12 | Ensaio | Todos falam; cada um explica o código dos colegas |

## 4. Rascunho do modelo de dados (para a etapa de modelagem)

- **Usuario** (`AbstractUser`) com `papel`: `SOLICITANTE`, `COORDENADOR`, `TECNICO`.
- **Local** (bloco/sala) e **TipoEquipamento** — tabelas para permitir filtro (US4) e seed.
- **Chamado**: solicitante, local, tipo de equipamento, descrição, `status` (aberto, atribuído, em andamento, concluído, cancelado, recusado), prioridade, técnico, prazo, motivo da recusa, descrição da solução, carimbos de tempo (criado, atribuído, iniciado, concluído, cancelado/recusado).
- **HistoricoChamado** (opcional): quem mudou o status e quando — ajuda na US7 e na demonstração.

Regras que nascem no domínio (não na view), para valerem igual pela tela e pela API:

| Regra | História | Recusa oficial |
| --- | --- | --- |
| Máx. 3 chamados ativos por solicitante; local e descrição obrigatórios | US1 | — |
| Solicitante só vê/acessa os próprios chamados | US2 | — |
| Cancelar só se aberto ou atribuído | US3 | — |
| Técnico com 5 ordens atribuídas/em andamento não recebe outra | US4 | **Recusa 1** |
| Recusar exige motivo e status aberto/atribuído | US5 | — |
| Só o técnico designado inicia o atendimento | US9 | **Recusa 2** |
| Conclusão exige descrição com ≥ 20 caracteres | US10 | **Recusa 3** |

## 5. Uso de IA (seção 13 da especificação)

| Exigência | Como vamos cumprir |
| --- | --- |
| Cada integrante explica qualquer parte | Revisão cruzada em todo PR; no ensaio, cada um apresenta código que não escreveu |
| Commit assinado por quem fez | Cada um commita o próprio trabalho, da própria máquina, com assinatura SSH |
| Configuração do assistente versionada | `CLAUDE.md` na raiz; `.claude/` (agentes/skills/comandos que criarmos) versionada |
| Planos e specs gerados por IA em `docs/` | Este plano, a modelagem do banco e quebras de tarefas vão para `docs/` |
| Registro de prompts | `PROMPTS.md` na raiz, uma entrada por prompt que gerou algo que ficou, com a linha **Resultado** (aceito como veio / aceito com ajustes / descartado) |
| Nada de credenciais nesses arquivos | Tokens (ex.: Trello) ficam fora do repositório |

## 6. Organização com o Trello

Quadro do grupo: https://trello.com/b/BTALfjm8/projeto-rad-ifdesk (criado por Pedro Lucas).

Listas por frente — `Backlog - Backend` (SU01–SU13, Suetone), `Backlog - Frontend` (PA01–PA17, Pedro Arthur), `Backlog - Infra` (PL01–PL21, Pedro Lucas), `Backlog - Team` (TEAM01–04) — mais `Recursos` e `Concluído`. O cartão referencia o PR; o PR referencia o cartão (ex.: `feat: modelos de chamado (SU01)`).
