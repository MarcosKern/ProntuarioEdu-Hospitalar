# Testes unitários

Testar regras sem banco, coordenação dos Controllers com substitutos simples e formatação das Views. Se o teste exigir persistência real, ele pertence à integração.

Na etapa 1 do [card F01](../../docs/F01.md), foram implementados:

- `test_settings.py`: URL MySQL obrigatória e completa, driver/porta válidos, precedência do ambiente, parâmetros reservados e mensagens sem credenciais.
- `test_startup.py`: inicialização FastAPI e documentação sem conectar ao MySQL nem criar administrador automaticamente.

A etapa 3 acrescenta `test_contracts.py`, com entradas/saídas tipadas e credenciais fora das representações textuais, e `test_pagination.py`, com limites, campos públicos e consistência da página.

De `backend`, no terminal Linux/Codespaces, com as dependências instaladas:

```bash
env MYSQL_TEST_URL= MYSQL_TEST_ALLOW_RESET= .venv/bin/python -m pytest -q tests/unit
```

As URLs são configurações isoladas dos testes, sem conexão a servidores. As variáveis MySQL de teste ficam vazias nesse comando para não acionar o reset de integração do `conftest.py`.
