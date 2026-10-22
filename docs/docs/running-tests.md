# Testes e cobertura

```bash
poetry run pytest
poetry run pytest tests/unit tests/integration
poetry run ruff check .
poetry run ruff format --check .
poetry run mypy
poetry run pip-audit
poetry run mkdocs build --strict -f docs/mkdocs.yml
```

O comando padrão executa unitários. A cobertura mede linhas de todo o pacote `f1`, incluindo módulos não importados; o mínimo de aceitação é 50%. Não excluir módulos nem reduzir o limite para obter sucesso. Cobertura não substitui asserções relevantes.

Fixtures são sintéticas e não alimentam o produto. MockTransport simula o HTTP; tmp_path isola arquivos. AppTest executa filtros e as cinco visões Streamlit sem servidor nem rede real. A integração usa os adaptadores e arquivos reais, mas a fonte HTTP é simulada.

Para verificação manual, abra uma sessão histórica real, navegue pelas visões, baixe uma tabela e reinicie a aplicação. Confirme a proveniência e a reutilização dos snapshots. Não tornar esse smoke test de rede obrigatório em cada PR.
