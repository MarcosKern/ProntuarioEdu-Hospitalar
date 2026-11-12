# ADR 0008 — MySQL de desenvolvimento com inicialização do SQL

Status: implementação solicitada pelo responsável para testar o contêiner com o SQL e disponibilizar o banco pronto para conexão.

## Decisão

Adicionar `backend/compose.mysql.yaml` como modo explícito de desenvolvimento, combinado com o Compose base. O serviço MySQL 8.4 usa imagem oficial fixada por digest e embarca o SQL revisado em seu diretório de inicialização. O entrypoint importa o schema somente quando o volume está vazio. O backend aguarda o health check do MySQL, que confirma conexão TCP e as contagens de tabelas, FKs e CHECKs do domínio.

O script `backend/scripts/mysql_dev.py` prepara credenciais aleatórias em `.env.mysql`, ignorado pelo Git e pelo contexto de build, sem sobrescrever `.env` ou regenerar senhas existentes. A API usa destino interno explícito `mysql:3306`; uma `DATABASE_URL` exportada no Codespace não muda esse destino. A senha root é fornecida somente ao MySQL.

## Limites

O Compose base mantém conexão com MySQL externo. A inicialização do schema de domínio é autorizada apenas neste modo de desenvolvimento; não é adicionada a hooks do Codespaces, às migrações existentes ou ao servidor externo. Models e rotas clínicas permanecem pendentes. Não há carga de dados de demonstração.

A porta SQL é publicada em loopback, o volume preserva o banco e o health check não substitui migrações futuras. A conta técnica de desenvolvimento permite DDL e triggers; o servidor deste modo habilita `log_bin_trust_function_creators`. Produção exige contas separadas, privilégios mínimos e TLS, conforme a ADR 0004.

## Validação

O modo independente `backend/compose.test.yaml` usa credenciais públicas e fixas, conforme solicitação posterior do responsável. Ele inicializa também `prontuario_test`, separado do banco da API, em volume próprio. `scripts/test_env.py` sobe o ambiente, aguarda os health checks e só então imprime as conexões; o modo de desenvolvimento mantém suas credenciais privadas. O script de testes não carrega implicitamente `.env` e não passa a senha root à API.

Construção das imagens, inicialização automática do SQL, aplicação do Alembic técnico, `/health`, `/docs`, verificação de constraints e reinício com o mesmo volume são testados em projeto Compose descartável. Os dados de teste são revertidos; nenhum banco real é acessado.
