#!/usr/bin/env bash
# Divide o trabalho da SU01 em commits semânticos, cada um passando sozinho pela esteira.
# Uso (na raiz do repositório, na branch feat/su01-modelagem-banco): bash scripts/commits-su01.sh
#
# Por que o stash: o pre-commit não esconde arquivos não rastreados durante os hooks, e o
# hook de testes descobre tudo que está no disco. Sem esconder `tickets/` no commit do
# `accounts`, o Django tentaria carregar um app fora do INSTALLED_APPS e o commit falharia.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

cp config/settings.py /tmp/settings-su01.py

# 1) build — sozinho, sem nenhum app novo no disco
git stash push --include-untracked --quiet -m su01-apps -- accounts tickets config/settings.py
git add pyproject.toml
git commit -m "build: exclui migrations geradas do lint do ruff"
git stash pop --quiet

# 2) feat — usuário customizado (settings ainda sem o app tickets)
git stash push --include-untracked --quiet -m su01-tickets -- tickets
sed -i.bak '/^    "tickets",$/d' config/settings.py && rm config/settings.py.bak
git add accounts config/settings.py
git commit -m "feat: adiciona usuário customizado com papel (SU01)" \
  -m "AUTH_USER_MODEL = accounts.User com o campo role (SOLICITANTE, COORDENADOR, TECNICO). Precisa existir antes de qualquer migration de app próprio. Inclui admin e testes unitários."
git stash pop --quiet

# 3) feat — chamados, locais e tipos de equipamento
cp /tmp/settings-su01.py config/settings.py
git add tickets config/settings.py
git commit -m "feat: adiciona modelos de chamado, local e tipo de equipamento (SU01)" \
  -m "Ticket concentra chamado e ordem de serviço, com status, prioridade, prazo por SLA e um carimbo de tempo por transição. CheckConstraint exige técnico e prioridade em atribuído/em andamento/concluído. Inclui querysets active/technician_load/overdue, admin e testes unitários."

# 4) docs — plano e modelagem
git add docs
git commit -m "docs: registra plano de desenvolvimento e modelagem do banco (SU01)"

# 5) docs — artefatos de IA
git add CLAUDE.md PROMPTS.md scripts/commits-su01.sh
git commit -m "docs: adiciona CLAUDE.md, registro de prompts e script de commits da SU01"

rm -f /tmp/settings-su01.py
git log --oneline --show-signature -5
