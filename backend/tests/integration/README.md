# Testes de integração

A suíte verifica rotas, tokens, limites, SQL real em **MySQL externo de teste** e migrações. Não utiliza banco em arquivo. Siga a [preparação da suíte](../README.md) antes de executar.

Use banco descartável separado (`MYSQL_TEST_URL`, nome iniciado por `prontuario_test`). A fixture apaga tabelas técnicas entre casos. Sem essa variável, verificações que precisam do banco são puladas. Nunca use o banco de desenvolvimento ou produção, nem rode a suíte em paralelo no mesmo banco.

`test_development.py` cobre SQL, schema e identidade; `test_security.py` verifica configuração e controles HTTP/permissões; `test_mysql.py` verifica triggers de auditoria. Testes usam dados transitórios e não carregam cadastros na aplicação. `test_authentication.py` e `test_admin.py` verificam login local e autorização com MySQL isolado; funcionalidades clínicas exigem suas próprias validações futuras.

Na [etapa 2 do F01](../../docs/F01.md#etapa-2--resultado), `test_transactions.py` cobre commit, rollback, falhas de constraint e liberação das conexões do pool. `test_migrations.py` verifica as revisões incrementais, InnoDB/UTC, ausência de cadastros automáticos, preservação dos dados ao reaplicar head e compatibilidade dos Models com o schema técnico. Esses testes exigem o MySQL separado e a confirmação de reset descritos acima.
