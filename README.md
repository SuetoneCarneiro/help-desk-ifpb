# help-desk-ifpb
Sistema de Help Desk para o IFPB - Campus João Pessoa

## Dependências com uv

O projeto usa o [uv](https://docs.astral.sh/uv/) para gerenciar dependências e o ambiente virtual.
As dependências ficam declaradas no `pyproject.toml` e travadas no `uv.lock`; os dois arquivos são versionados.
Não existe `requirements.txt` mantido à mão.

Instalação do uv (Windows / Linux e macOS):

```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Instalar as dependências (cria o `.venv` com as versões exatas do `uv.lock`):

```bash
uv sync
```

Rodar o projeto e os testes:

```bash
uv run manage.py runserver
uv run manage.py test
```

Adicionar ou remover dependências (atualiza `pyproject.toml` e `uv.lock` juntos):

```bash
uv add <pacote>
uv add --dev <pacote>
uv remove <pacote>
```

## Esteira de qualidade (pre-commit)

Os hooks ficam em `.pre-commit-config.yaml` e rodam automaticamente antes de cada commit.
**Todo integrante precisa instalá-los** depois do `uv sync`:

```bash
uv run pre-commit install --install-hooks
```

O arquivo define `default_install_hook_types: [pre-commit, commit-msg]`, então esse único comando instala também o hook que valida a mensagem do commit.

Para rodar todas as verificações manualmente:

```bash
uv run pre-commit run --all-files
```

| Hook | O que verifica |
| --- | --- |
| `ruff-check` / `ruff-format` | Lint (com correção automática) e formatação |
| `uv-export-audit` + `pip-audit` | Vulnerabilidades nas dependências travadas |
| `conventional-pre-commit` | Mensagem no padrão Conventional Commits (estágio `commit-msg`) |
| `django-check` | `manage.py check` |
| `django-migrations` | Alteração de model sem migration (`makemigrations --check`) |
| `cobertura-testes` / `cobertura-relatorio` | Testes com `--shuffle` e cobertura mínima de 95% (`fail_under` no `pyproject.toml`) |

**Por que o pip-audit lê um arquivo exportado, e não o `pyproject.toml`:** o pip-audit não lê o `uv.lock`, e apontado para `.` ele audita as faixas de versão declaradas no `pyproject.toml`, não as versões que o `uv sync` realmente instala.
Por isso o hook `uv-export-audit` gera `requirements-audit.txt` a partir do `uv.lock` (`uv export --format requirements.txt`) e o `pip-audit` audita esse arquivo com `-r`.
O arquivo é gerado a cada execução e está no `.gitignore`; ele não é um `requirements.txt` mantido à mão.

**Por que a cobertura são dois hooks:** a especificação sugere `bash -c "... && ..."`, mas no Windows o `bash` do sistema costuma ser o do WSL, que roda fora do ambiente do uv.
Separar em `coverage run` e `coverage report` mantém o mesmo efeito em Windows, Linux e macOS.
