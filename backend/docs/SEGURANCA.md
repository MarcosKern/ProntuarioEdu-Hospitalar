# Segurança e operação

Para executar a API, use o [roteiro principal](../README.md). Esta referência descreve controles e responsabilidades operacionais. O comportamento de login/tokens está em [autenticação](AUTENTICACAO.md).

## Configuração

`APP_ENV`: development, test ou production. `ALLOWED_HOSTS` e `CORS_ORIGINS` são arrays JSON explícitos. `RATE_LIMIT` limita chamadas `/api/` por IP em janela de 60 segundos; `MAX_BODY_BYTES` limita corpos inclusive sem Content-Length. Em desenvolvimento sem Redis há limite local, inadequado a múltiplos processos. Em produção Redis é obrigatório e falhas do limitador bloqueiam chamadas com 503. REDIS_CONNECT_TIMEOUT e REDIS_SOCKET_TIMEOUT são limitados a (0, 30] segundos, com padrão 2 segundos cada e sem repetição automática. Os timeouts não podem ser sobrescritos pela URL.

O servidor ignora headers de proxy por padrão. Não confie livremente em X-Forwarded-For. Na implantação, limite acesso direto à API, configure proxies confiáveis e TLS no gateway; dimensione limites por usuário/origem conforme tráfego real, sobretudo quando vários usuários compartilham IP. Configure também timeout de leitura e limites no gateway.

Em produção a validação exige MySQL com CA confiável, Redis via `rediss://` e `AUTH_JWT_SECRET` aleatório de pelo menos 32 bytes. Certificado e hostname do Redis são verificados. `authenticate_request` aceita somente JWT HS256 com assinatura, emissor, audiência, expiração, IDs e escopos válidos. Consulta a sessão e o usuário no MySQL em cada requisição, falhando com 503 se a dependência estiver indisponível.

Hashes de senha, rotação de refresh e revogação de sessões são detalhados no [contrato de autenticação](AUTENTICACAO.md#como-validar-acesso-e-sessão). Recuperação de senha, MFA e armazenamento seguro nos clientes ainda precisam de implementação própria.

## Permissões e auditoria

O [primeiro administrador](../README.md#4-criar-o-administrador-da-aplicação) é criado por prompt explícito em `cadastro__usuarios`, com senha em hash, perfil `ADMINISTRADOR` e `USUARIO_GERENCIAR`. `controllers/admin.py` verifica o cadastro e a concessão ativa após validar token e sessão. Contas externas só são convertidas explicitamente, mantendo ID e concessões; revogações não são restauradas. A conta não recebe bypass de prontuários. Configuração JWT/conexão fica em variáveis privadas ou gerenciador de segredos; não há realm, certificado próprio de identidade ou cofre adicional.


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

CI em `.github/workflows/backend.yml` executa Ruff, pytest com MySQL isolado, pip-audit e Trivy para vulnerabilidades e segredos da imagem da API. HIGH/CRITICAL reprovam o job `image`; os checks continuam `test` e `image`. O servidor de identidade e sua cadeia Java foram removidos conforme escolha do responsável; não há imagem Keycloak em uso ou no build. Não usa pull_request_target nem publica imagens. Credenciais fixas do MySQL de CI são efêmeras, exclusivas do runner. Os testes não carregam dados na aplicação.


Os comandos e destinos descartáveis de validação local estão no [guia de testes](../tests/README.md). Resultados de CI devem ser conferidos no commit em revisão, não inferidos de relatórios antigos.

## Produção: requisitos ainda externos

Configurar políticas de acesso e gestão/rotação da chave JWT; TLS e gateway; segredos gerenciados; usuários de banco mínimos separados; Redis privado com autenticação/TLS; métricas privadas e alertas; retenção aprovada e rotina de backup. A infraestrutura implementada não significa que o produto esteja liberado para dados clínicos reais.

## Base da imagem e correções de sistema

A imagem usa Python 3.12 com Alpine 3.23, fixada por digest no Dockerfile. A escolha substitui a base Debian que apresentou vulnerabilidades HIGH em bibliotecas do sistema. Alpine usa musl em vez de glibc: novas dependências nativas precisam ser verificadas nessa plataforma. Não copiar bibliotecas binárias de imagens Debian para essa imagem.

O Dockerfile fixa a base oficial Python 3.12.16/Alpine 3.23 e instala `krb5-libs=1.22.3-r0`, correção publicada no ramo Alpine `3.23-stable`. Essa etapa mantém a verificação TLS, aceita a CA opcional pelo segredo BuildKit `proxy_ca` e falha se não conseguir instalar o pacote; não libera uma imagem com a versão vulnerável por tolerância de erro.

O registro histórico de falha de rede no build está no [F01](../../docs/historico/F01.md). Ele não descreve necessariamente o estado atual da rede ou da imagem: use os resultados do workflow do commit em revisão.

O usuário de execução continua sem privilégios (UID 1000, preservando o usuário anterior de desenvolvimento). O MySQL permanece externo, usando PyMySQL. A mudança de distribuição não muda o contrato HTTP nem as regras MVC. Dependências continuam fixadas em requirements.txt; a CI verifica a imagem completa com a mesma política de vulnerabilidades e segredos.

Manter a base atualizada: consultar a imagem oficial Python 3.12/Alpine, verificar o novo digest, reconstruir, executar testes incluindo MySQL e repetir o scan completo. Um resultado limpo em HIGH/CRITICAL é uma observação daquela base de vulnerabilidades e imagem, não garantia permanente ou ausência de achados menores. Não usar ignore-unfixed, supressões globais ou remoção do scan para liberar a imagem.

## Auditoria contínua e diagnóstico

O workflow Backend validation pode ser disparado manualmente e agenda execução semanal em UTC, além de PR/push-main. Instala o lock dev para testes; a imagem instala somente runtime. Dependabot cobre pip, Docker e Actions. CodeQL tem workflow Python dedicado com ações fixadas por SHA e permissão restrita de publicação de análises. Confira seu resultado na aba Actions; se houver default setup habilitado, o administrador deve escolher entre o setup padrão e o avançado para evitar duplicação. A configuração nativa de code_quality permanece sob controle do administrador.

As respostas esperadas são descritas por ErrorResponse no OpenAPI, conforme cada rota. Erros inesperados registram request ID, classe, rota parametrizada e localização de código sem mensagem de exceção, variáveis locais, corpo, token ou URL de conexão. Os logs não devem receber posteriormente `str(exception)` ou traceback com locais, que podem reintroduzir exposição de dados.

Leitura/escrita SQL e espera por pool agora têm limites explícitos. Validar esses limites com o operador do banco externo; timeouts não substituem índices, dimensionamento, monitoramento ou uma estratégia de idempotência.
