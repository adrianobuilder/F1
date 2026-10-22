# Contribuição

Seguir o SKILL.md da raiz: Poetry exclusivamente; pacotes em src; funções públicas tipadas; docstrings Google; Ruff para lint, imports e formato. Contratos e regras de negócio não devem depender de Streamlit.

Use branches feat/tema, fix/tema ou docs/tema e commits claros, preferencialmente Conventional Commits. PRs devem incluir testes de mudanças de comportamento e atualização da documentação. Revisar o poetry.lock junto das dependências. Não versionar ambientes, snapshots, credenciais ou dados sensíveis.

O CI verifica manifest/lock, Ruff, testes e cobertura, mypy, auditoria e MkDocs. Configure o job quality como obrigatório na proteção da branch, com code review conforme política da equipe. O YAML sozinho não impede merge. Não há publicação ou deploy automático.

Antes da entrega, informar os comandos realmente executados, seus resultados e limitações. Não ignorar falhas ou declarar testes aprovados sem execução. O projeto deve funcionar em Windows e no runner Linux.
