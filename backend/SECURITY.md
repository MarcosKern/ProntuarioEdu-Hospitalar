# Segurança e operação

## Iniciar o ambiente

Siga [MySQL externo](MYSQL.md) para configurar DATABASE_URL, CA, migrações e testes. Compose não inicia servidor de banco. O provedor OIDC continua externo e precisa ser configurado.

## Configuração

`APP_ENV`: development, test ou production. `ALLOWED_HOSTS` e `CORS_ORIGINS` são arrays JSON explícitos. `RATE_LIMIT` limita chamadas `/api/` por IP em janela de 60 segundos; `MAX_BODY_BYTES` limita corpos inclusive sem Content-Length. Em desenvolvimento sem Redis há limite local, inadequado a múltiplos processos. Em produção Redis é obrigatório e falhas do limitador bloqueiam chamadas com 503. REDIS_CONNECT_TIMEOUT e REDIS_SOCKET_TIMEOUT são limitados a (0, 30] segundos, com padrão 2 segundos cada e sem repetição automática. Os timeouts não podem ser sobrescritos pela URL.

O servidor ignora headers de proxy por padrão. Não confie livremente em X-Forwarded-For. Na implantação, limite acesso direto à API, configure proxies confiáveis e TLS no gateway; dimensione limites por usuário/origem conforme tráfego real, sobretudo quando vários usuários compartilham IP. Configure também timeout de leitura e limites no gateway.

Em produção a validação exige MySQL com CA confiável configurada, Redis via `rediss://` e todos os endereços/identificadores OIDC. Certificado e hostname do Redis são verificados; uma CA privada pode ser definida em REDIS_SSL_CA. O mecanismo atual aceita tokens RS256 e verifica assinatura, issuer, audience, expiração e subject. Revogação imediata e logout global dependem do provedor e da estratégia acordada; JWT já emitido pode permanecer válido até expirar. Use duração curta e estratégia de revogação/introspecção se exigida pelo negócio. Não há provedor implantado automaticamente.

## Permissões e auditoria

`controllers/permissions.py::require_record_access` exige concessão explícita em `record_permissions`, sem bypass administrativo implícito. Use identidade validada pelo servidor, nunca campos do corpo da requisição. Falha de banco/auditoria bloqueia a operação. Nenhum endpoint clínico foi criado enquanto a regra de perfis não for informada.

A concessão tem escopo de um registro e ação read/write. Ela não substitui políticas clínicas, vínculo organizacional ou aprovação formal: essas regras precisam ser definidas antes de concessões reais. IDs não comprovam existência de prontuários. Não dê acesso direto a essa tabela a usuários finais.

`audit_events` registra decisão, identidade, registro, ação, horário UTC e request ID, sem corpo clínico. O trigger MySQL impede alteração/exclusão usuais. Separe credenciais de migração e runtime em produção e proíba TRUNCATE/DDL do usuário da API; o dono da tabela e superusuários continuam privilegiados. MySQL 8.4 tem triggers de imutabilidade na revisão 0002; administradores e operações DDL continuam privilegiados. Defina retenção e descarte autorizado com responsáveis pelo negócio/LGPD; não implementar exclusão automática sem essa decisão.

## Logs e métricas

Cada resposta processada recebe X-Request-ID. Logs estruturados não gravam URL completa, query, corpo ou token. Uvicorn access logs ficam desabilitados nos comandos do projeto. `/metrics` expõe contagem por rota/status e histograma de latência somente fora de produção. Não há prontuários ou identificadores como labels. Para produção, publicar métricas por canal privado e configurar alertas/SLOs da infraestrutura escolhida; não abrir esse endpoint na Internet.

## Migrações

De `backend`, com venv ativo: `python -m alembic upgrade head`. Para evoluir schema: `python -m alembic revision --autogenerate -m "descricao"`, revisar o arquivo e testar ida/compatibilidade/recuperação em banco isolado. Não executar downgrade destrutivo em produção sem plano aprovado. A migração inicial cria tabelas técnicas vazias.

## Backup e restauração isolada

Use os procedimentos de [backup MySQL remoto](MYSQL.md#backup-remoto-e-recuperação-isolada). A verificação restaura em banco separado; a conta operacional precisa de privilégios próprios. Mantenha chave e backup separados e defina retenção/RPO/RTO com os responsáveis.

## Verificação automática

CI em `.github/workflows/backend.yml` executa Ruff, pytest com MySQL isolado, pip-audit e Trivy (imagem e segredos). Não usa pull_request_target nem publica imagens. Credencial fixa do serviço MySQL de CI é efêmera e exclusiva do runner; não é uma conta da aplicação. Os testes não carregam dados na aplicação.

Local: `python -m pytest -q`, `python -m ruff check src tests scripts` e `python -m pip_audit -r requirements.txt` e `python -m pip_audit -r requirements-dev.txt`. O teste MySQL exige confirmação `MYSQL_TEST_ALLOW_RESET` igual ao nome exato do banco e `MYSQL_TEST_URL` apontando a banco descartável com nome iniciado por `prontuario_test`; sem isso é explicitamente pulado.

## Produção: requisitos ainda externos

Configurar provedor OIDC e permissões reais; TLS e gateway; segredos gerenciados; usuários de banco mínimos separados; Redis privado com autenticação/TLS; métricas privadas e alertas; retenção aprovada e rotina de backup. A infraestrutura implementada não significa que o produto esteja liberado para dados clínicos reais.

## Base da imagem e correções de sistema

A imagem usa Python 3.12 com Alpine 3.23, fixada por digest no Dockerfile. A escolha substitui a base Debian que apresentou vulnerabilidades HIGH em bibliotecas do sistema. Alpine usa musl em vez de glibc: novas dependências nativas precisam ser verificadas nessa plataforma. Não copiar bibliotecas binárias de imagens Debian para essa imagem.

O usuário de execução continua sem privilégios (UID 1000, preservando o usuário anterior de desenvolvimento). O MySQL permanece externo, usando PyMySQL. A mudança de distribuição não muda o contrato HTTP nem as regras MVC. Dependências continuam fixadas em requirements.txt; a CI verifica a imagem completa com a mesma política de vulnerabilidades e segredos.

Manter a base atualizada: consultar a imagem oficial Python 3.12/Alpine, verificar o novo digest, reconstruir, executar testes incluindo MySQL e repetir o scan completo. Um resultado limpo em HIGH/CRITICAL é uma observação daquela base de vulnerabilidades e imagem, não garantia permanente ou ausência de achados menores. Não usar ignore-unfixed, supressões globais ou remoção do scan para liberar a imagem.

## Auditoria contínua e diagnóstico

O workflow Backend validation pode ser disparado manualmente e agenda execução semanal em UTC, além de PR/push-main. Instala o lock dev para testes; a imagem instala somente runtime. Dependabot cobre pip, Docker e Actions. CodeQL tem workflow Python dedicado com ações fixadas por SHA e permissão restrita de publicação de análises. Ele só será validado após execução no GitHub; se houver default setup habilitado, o administrador deve escolher entre o setup padrão e o avançado para evitar duplicação. A configuração nativa de code_quality permanece sob controle do administrador.

As respostas esperadas são descritas por ErrorResponse no OpenAPI, conforme cada rota. Erros inesperados registram request ID, classe, rota parametrizada e localização de código sem mensagem de exceção, variáveis locais, corpo, token ou URL de conexão. Os logs não devem receber posteriormente `str(exception)` ou traceback com locais, que podem reintroduzir exposição de dados.

Leitura/escrita SQL e espera por pool agora têm limites explícitos. Validar esses limites com o operador do banco externo; timeouts não substituem índices, dimensionamento, monitoramento ou uma estratégia de idempotência.
