# Segurança e operação

## Iniciar o novo ambiente

1. Instale `requirements.txt` no venv.
2. Copie `.env.example` para `.env` se não existir; preserve configurações já existentes.
3. Gere uma senha local aleatória e adicione `POSTGRES_PASSWORD` ao `.env` de forma segura. Não use a senha em URLs no histórico do terminal nem versionada. O Compose constrói a URL internamente.
4. Execute `docker compose up --build -d --wait`. O banco e Redis ficam apenas na rede interna. As migrações são aplicadas antes de iniciar o servidor.
5. Confira `/health`, `/docs` e testes. Não há usuário, prontuário ou concessão inicial. O volume PostgreSQL é novo; dados SQLite antigos não são migrados automaticamente.

`python scripts/dev.py --setup` continua disponível com SQLite local e aplica as migrações. Configuração `.env` é carregada e validada pelo servidor; não é preciso executá-la no shell. A senha PostgreSQL não é necessária para esse modo.

## Configuração

`APP_ENV`: development, test ou production. `ALLOWED_HOSTS` e `CORS_ORIGINS` são arrays JSON explícitos. `RATE_LIMIT` limita chamadas `/api/` por IP em janela de 60 segundos; `MAX_BODY_BYTES` limita corpos inclusive sem Content-Length. Em desenvolvimento sem Redis há limite local, inadequado a múltiplos processos. Em produção Redis é obrigatório e falhas do limitador bloqueiam chamadas.

O servidor ignora headers de proxy por padrão. Não confie livremente em X-Forwarded-For. Na implantação, limite acesso direto à API, configure proxies confiáveis e TLS no gateway; dimensione limites por usuário/origem conforme tráfego real, sobretudo quando vários usuários compartilham IP. Configure também timeout de leitura e limites no gateway.

Em produção a validação exige PostgreSQL, Redis e todos os endereços/identificadores OIDC. O mecanismo atual aceita tokens RS256 e verifica assinatura, issuer, audience, expiração e subject. Revogação imediata e logout global dependem do provedor e da estratégia acordada; JWT já emitido pode permanecer válido até expirar. Use duração curta e estratégia de revogação/introspecção se exigida pelo negócio. Não há provedor implantado automaticamente.

## Permissões e auditoria

`controllers/permissions.py::require_record_access` exige concessão explícita em `record_permissions`, sem bypass administrativo implícito. Use identidade validada pelo servidor, nunca campos do corpo da requisição. Falha de banco/auditoria bloqueia a operação. Nenhum endpoint clínico foi criado enquanto a regra de perfis não for informada.

A concessão tem escopo de um registro e ação read/write. Ela não substitui políticas clínicas, vínculo organizacional ou aprovação formal: essas regras precisam ser definidas antes de concessões reais. IDs não comprovam existência de prontuários. Não dê acesso direto a essa tabela a usuários finais.

`audit_events` registra decisão, identidade, registro, ação, horário UTC e request ID, sem corpo clínico. O trigger PostgreSQL impede alteração/exclusão usuais. Separe credenciais de migração e runtime em produção e proíba TRUNCATE/DDL do usuário da API; o dono da tabela e superusuários continuam privilegiados. SQLite não tem o trigger de imutabilidade. Defina retenção e descarte autorizado com responsáveis pelo negócio/LGPD; não implementar exclusão automática sem essa decisão.

## Logs e métricas

Cada resposta processada recebe X-Request-ID. Logs estruturados não gravam URL completa, query, corpo ou token. Uvicorn access logs ficam desabilitados nos comandos do projeto. `/metrics` expõe contagem por rota/status e histograma de latência somente fora de produção. Não há prontuários ou identificadores como labels. Para produção, publicar métricas por canal privado e configurar alertas/SLOs da infraestrutura escolhida; não abrir esse endpoint na Internet.

## Migrações

De `backend`, com venv ativo: `python -m alembic upgrade head`. Para evoluir schema: `python -m alembic revision --autogenerate -m "descricao"`, revisar o arquivo e testar ida/compatibilidade/recuperação em banco isolado. Não executar downgrade destrutivo em produção sem plano aprovado. A migração inicial cria tabelas técnicas vazias.

## Backup e restauração isolada

De `backend`, com PostgreSQL Compose ativo e venv:

```bash
mkdir -p backups
python scripts/backup.py keygen --key-file backups/storage.fernet
python scripts/backup.py backup --key-file backups/storage.fernet --file backups/database.backup.enc
python scripts/backup.py verify --key-file backups/storage.fernet --file backups/database.backup.enc
```

O backup usa pg_dump consistente, criptografa o arquivo e não sobrescreve arquivos existentes. A verificação descriptografa e restaura em banco separado com nome aleatório, consulta as tabelas e remove esse banco; nunca sobrescreve o principal. Mantenha a chave separada dos backups em armazenamento seguro: perder a chave perde a recuperação. Os caminhos acima são conveniência local, não organização recomendada para armazenamento externo. Não enviar a chave ao Git, logs ou chat.

O script é destinado ao Compose de desenvolvimento e processa o dump em memória: para bancos grandes, adotar ferramenta de backup com streaming criptografado, armazenamento externo e gestão de chaves. Produção exige agendamento, retenção, cópia externa, controle de acesso, alertas de falha e exercícios periódicos de restauração/RPO/RTO. Não foram inventados prazos clínicos ou de retenção.

## Verificação automática

CI em `.github/workflows/backend.yml` executa Ruff, pytest com PostgreSQL isolado, pip-audit e Trivy (imagem e segredos). Não usa pull_request_target nem publica imagens. Credencial fixa do serviço PostgreSQL de CI é efêmera e exclusiva do runner; não é uma conta da aplicação. Os testes não carregam dados na aplicação.

Local: `python -m pytest -q`, `python -m ruff check src tests scripts` e `python -m pip_audit -r requirements.txt`. O teste PostgreSQL exige `POSTGRES_TEST_URL` apontando a banco descartável com nome iniciado por `prontuario_test`; sem isso é explicitamente pulado.

## Produção: requisitos ainda externos

Configurar provedor OIDC e permissões reais; TLS e gateway; segredos gerenciados; usuários de banco mínimos separados; Redis privado com autenticação/TLS; métricas privadas e alertas; retenção aprovada e rotina de backup. A infraestrutura implementada não significa que o produto esteja liberado para dados clínicos reais.
