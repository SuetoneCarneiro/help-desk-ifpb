# PA01 — Estrutura visual do Help Desk IFPB

Responsável: Pedro Arthur de Holanda Nery.

## Objetivo

Criar a base visual compartilhada com templates Django. A US1 e a US10
poderão reutilizar os mesmos campos, botões, alertas e padrões de formulário.

## Decisões

- Usar templates/base.html como layout das páginas públicas e autenticadas.
- Exibir menu lateral no desktop e navegação recolhível no celular.
- Mostrar ao solicitante os links do painel, da listagem e da abertura.
- Mostrar ao coordenador e ao técnico os destinos que já possuem rota.
- Manter autorização nas views e políticas, e regras de negócio nos serviços.
- Usar CSS e JavaScript locais em accounts/static/helpdesk/.
- Usar verde nas ações principais, texto legível e foco visível por teclado.
- Indicar o status por texto e cor, preservando o rótulo do model.
- Preservar POST e CSRF no logout, mensagens do Django e erros de formulário.

## Validação

Conferir navegação por papel, abertura do menu móvel, mensagens, formulário
de abertura, detalhe e listagem. Executar os testes Django com --shuffle,
medir a cobertura e rodar a esteira de pre-commit.
