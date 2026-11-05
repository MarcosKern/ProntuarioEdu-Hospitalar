# Testes de integração

Executar operações HTTP contra a aplicação e banco isolados. Verificar rotas, autenticação, autorização por registro, gravação, commit/rollback e mapeamento de erros. Usar dados sintéticos e limpar somente o banco de teste. Uma porta aberta não comprova funcionamento. `test_development.py` verifica SQL real em arquivo temporário, Swagger/OpenAPI e tokens JWT com chaves sintéticas, sem chamar provedor externo.
