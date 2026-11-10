# Testes do contrato da API

Conferir se métodos, caminhos, esquemas, códigos de resposta e segurança da API real correspondem ao OpenAPI. Desktop e Web dependem dessa estabilidade. Validar o documento é necessário, mas também testar requisições reais. A suíte inicial em `../integration/test_development.py` confere geração do schema e declaração OAuth2; uma suíte completa de contrato para funcionalidades futuras ainda precisa ser construída.

`test_swagger.py` verifica o Swagger no hostname encaminhado do Codespace, client ID público opcional, PKCE, retorno OAuth2 na mesma origem, ausência de persistência da autorização e segurança da operação de identidade. Não conecta ao MySQL quando `MYSQL_TEST_URL` está ausente. O teste de ocultação em produção permanece em `../integration/test_security.py`.
