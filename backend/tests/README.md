# Testes do Back-end MVC

- `unit/`: regras dos Models e lógica isolada dos Controllers/Views.
- `integration/`: rotas, autenticação, autorização, banco de teste e transações.
- `contract/`: correspondência entre respostas reais e OpenAPI.

Uma nova operação deve cobrir sucesso, entrada inválida, usuário sem acesso e falha de gravação quando aplicável. Use dados sintéticos e ambiente isolado. A suíte inicial usa pytest e está em `integration/test_development.py`; executar `python -m pytest -q` de `backend` com o venv ativo. Testes de funcionalidades clínicas ainda são futuros.
