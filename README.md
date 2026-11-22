# help-desk-ifpb
Sistema de Help Desk para o IFPB - Campus João Pessoa

## Configuração do ambiente de desenvolvimento

Passo a passo que **todo integrante** executa uma vez na própria máquina.
Ele configura o uv (dependências), o pre-commit (esteira de qualidade) e a assinatura de commits por SSH (selo Verified no GitHub).

### 1. Instalar o uv

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Linux / macOS:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Depois da instalação, feche e abra de novo o editor (VS Code, Cursor, PyCharm) e todos os terminais.**
Os terminais do editor herdam o PATH de quando o editor foi aberto; sem reiniciar, os hooks falham com `Executable 'uv' not found`.

Conferir:

```bash
uv --version
```

### 2. Clonar o projeto e instalar as dependências

```bash
git clone https://github.com/SuetoneCarneiro/help-desk-ifpb.git
cd help-desk-ifpb
uv sync
```

Quem já tem o repositório clonado roda `git switch main`, `git pull` e `uv sync`.
O `uv sync` cria o `.venv` com as versões exatas do `uv.lock`; não é preciso criar venv nem usar `pip install`.

Conferir:

```bash
uv run manage.py check
uv run manage.py test
```

### 3. Instalar a esteira de pre-commit

```bash
uv run pre-commit install --install-hooks
```

A saída precisa mostrar as duas linhas abaixo:

```
pre-commit installed at .git/hooks/pre-commit
pre-commit installed at .git/hooks/commit-msg
```

Validar (a primeira execução demora alguns minutos, porque baixa os ambientes dos hooks):

```bash
uv run pre-commit run --all-files
```

Todos os hooks devem aparecer como `Passed`.

### 4. Configurar a assinatura de commits por SSH

#### 4.1 Verificar se já existe uma chave SSH

Windows (PowerShell): `Test-Path "$env:USERPROFILE\.ssh\id_ed25519.pub"`

Linux / macOS: `ls ~/.ssh/id_ed25519.pub`

Se não existir, crie uma com o e-mail da sua conta do GitHub (Enter para aceitar o caminho padrão; a senha é opcional):

```bash
ssh-keygen -t ed25519 -C "seu-email-do-github@exemplo.com"
```

#### 4.2 Configurar o git

Use o mesmo e-mail que está verificado na sua conta do GitHub.

Windows (PowerShell):

```powershell
git config --global user.name "SeuUsuarioGitHub"
git config --global user.email "seu-email-do-github@exemplo.com"
git config --global gpg.format ssh
git config --global user.signingkey "$env:USERPROFILE\.ssh\id_ed25519.pub"
git config --global commit.gpgsign true
git config --global tag.gpgsign true
```

Linux / macOS:

```bash
git config --global user.name "SeuUsuarioGitHub"
git config --global user.email "seu-email-do-github@exemplo.com"
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
git config --global tag.gpgsign true
```

#### 4.3 Cadastrar a chave no GitHub como Signing Key

1. Copie a chave pública:
   - Windows: `Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | Set-Clipboard`
   - macOS: `pbcopy < ~/.ssh/id_ed25519.pub`
   - Linux: `cat ~/.ssh/id_ed25519.pub` e copie a saída
2. Abra [github.com/settings/ssh/new](https://github.com/settings/ssh/new).
3. Em **Key type**, escolha **Signing Key**, cole a chave e salve.

Mesmo que a chave já esteja cadastrada como *Authentication Key*, cadastre-a **de novo** como *Signing Key*: o GitHub trata as duas como tipos diferentes.

#### 4.4 Conferir o e-mail e ligar o vigilant mode

- Em [github.com/settings/emails](https://github.com/settings/emails), o e-mail do `git config` precisa estar na lista e verificado.
- Em [github.com/settings/ssh](https://github.com/settings/ssh), marque **Vigilant mode**.

#### 4.5 Opcional: não digitar a senha da chave a cada commit

Só é necessário se a chave tiver senha.

Windows: primeiro, num PowerShell **como administrador**:

```powershell
Get-Service ssh-agent | Set-Service -StartupType Automatic
Start-Service ssh-agent
```

Depois, num PowerShell normal:

```powershell
ssh-add "$env:USERPROFILE\.ssh\id_ed25519"
git config --global core.sshCommand "C:/Windows/System32/OpenSSH/ssh.exe"
git config --global gpg.ssh.program "C:/Windows/System32/OpenSSH/ssh-keygen.exe"
```

Linux / macOS:

```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

### 5. Padrões de trabalho do time

- **Branch pessoal:** `develop-<nome-sobrenome>`, por exemplo `develop-pedro-arthur` e `develop-suetone-carneiro`. O trabalho chega à `main` por pull request.
- **Mensagens de commit** no padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/), no formato `tipo: descrição`. O hook recusa o commit fora do padrão. Tipos aceitos: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.

  ```
  feat: abre chamado com local, tipo e descrição
  fix: corrige limite de chamados em aberto
  test: cobre recusa de atribuição acima de 5 ordens
  ```

- **Dependências:** sempre com `uv add` / `uv remove` (ver [Dependências com uv](#dependências-com-uv)), com commit do `pyproject.toml` e do `uv.lock` juntos.
- **Depois de puxar alterações de colegas**, rode `uv sync` para atualizar o ambiente.

### 6. Verificação final

1. Faça um commit na sua branch: os hooks devem rodar e passar.
2. `git push -u origin <sua-branch>`.
3. Abra o commit no GitHub e confira o selo **Verified**.

### Problemas comuns

| Sintoma | Causa e solução |
| --- | --- |
| `Executable 'uv' not found` nos hooks | O terminal ou o editor foi aberto antes de instalar o uv. Reinicie o editor por completo. |
| `ruff format ... Failed - files were modified` | O ruff já corrigiu a formatação. Rode `git add -A` e repita o commit. |
| `Conventional Commit ... Failed` | Mensagem fora do padrão. Use `tipo: descrição`. |
| `cobertura de testes (relatório) ... Failed` | Cobertura abaixo de 95%. Escreva testes para as linhas listadas em `Missing`. |
| `migrations pendentes ... Failed` | Model alterado sem migration. Rode `uv run manage.py makemigrations` e inclua o arquivo no commit. |
| Commit aparece como **Unverified** no GitHub | A chave foi cadastrada como *Authentication* em vez de *Signing*, ou o e-mail do commit não está verificado na conta. |

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
