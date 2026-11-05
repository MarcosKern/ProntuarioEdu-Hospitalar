# Testes do contrato da API

Conferir se métodos, caminhos, esquemas, códigos de resposta e segurança da API real correspondem ao OpenAPI. Desktop e Web dependem dessa estabilidade. Validar o documento é necessário, mas também testar requisições reais. A suíte inicial em `../integration/test_development.py` confere geração do schema e declaração OAuth2; uma suíte completa de contrato para funcionalidades futuras ainda precisa ser construída.
