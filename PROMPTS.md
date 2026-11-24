# Registro de prompts

Prompts usados com assistentes de IA que produziram algo que ficou no sistema (regra de negócio, modelo de dados, configuração da esteira, testes). Exigência da seção 13 da especificação.

Formato de cada entrada:

```
## AAAA-MM-DD — <integrante> — <objetivo>

Prompt:
> texto do prompt

Resultado: aceito como veio | aceito com ajustes — <quais> | descartado — <por quê>
```

---

## 2026-11-24 — Suetone — plano de desenvolvimento e organização do uso de IA

Ferramenta: Claude Code.

Prompt:
> Analise os arquivos [especificação do trabalho e proposta entregue] e faça um plano para desenvolvimento do projeto. Verifique as partes que falam sobre o uso de IA para que possamos organizar isso também. [...] verificar se há alguma task de infraestrutura que precisa ser feita antes de iniciar o backend.

Resultado: <!-- preencher: aceito como veio / aceito com ajustes / descartado --> plano em `docs/plano-desenvolvimento-backend.md`; cards PL04–PL08 movidos para Concluído no Trello.

## 2026-11-24 — Suetone — modelagem do banco (SU01)

Ferramenta: Claude Code.

Prompt:
> [Front-end decidido: templates Django.] Modelar o banco conforme o card SU01 do Trello: usuário com papel, chamado/ordem de serviço, categorias, local, status, prioridade, técnico, motivo da recusa, descrição da solução, datas de abertura/atribuição/início/conclusão e prazo.

Resultado: <!-- preencher: aceito como veio / aceito com ajustes / descartado --> apps `accounts` e `tickets`, migrations, admin, testes unitários e `docs/modelagem-banco.md`.

## 2026-11-24 — Suetone — autenticação e identificação dos papéis (SU02)

Ferramenta: Claude Code.

Prompt:
> Prepare para a task SU02. É possível fazer ou há algum bloqueio? [...] pode implementar a SU02

Resultado: aceito como veio 
plano em `docs/plano-su02-autenticacao.md`; login/logout por sessão, painel por papel, `accounts/permissions.py` (`role_required`, `RoleRequiredMixin`), página 403 e testes unitários e de integração.

## 2026-11-24 — Suetone — controle de acesso por papel (SU03)

Ferramenta: Claude Code.

Prompt:
> Preparar para SU03. [...] Qual seriam as vantagens e desvantagens de fazer da maneira que você propôs? [...] pode implementar a SU03. Deixe no plano uma explicação simples para essa decisão

Resultado: aceito com ajustes
`tickets/policies.py` (funções `can_*` e `ensure`), `Ticket.objects.visible_to(user)`, testes da matriz papel × operação e plano com a explicação da decisão em `docs/plano-su03-permissoes.md`; convenção registrada no `CLAUDE.md`.
