# MySQL externo: configuração atual

Este é o guia vigente para o banco do projeto. O padrão de todo o Back-end é **MySQL 8.4 + PyMySQL**, inclusive testes de integração.

## Preparar a conexão

Solicite ao responsável pelo servidor MySQL um banco vazio dedicado, usuário, privilégios e certificado CA quando aplicável. Não instale MySQL localmente para executar a aplicação. Não envie senhas pelo chat ou pelo Git.

De `backend`, copie `.env.example` para `.env` apenas se ainda não existir. Preencha privadamente:

```dotenv
APP_ENV=development
DATABASE_URL=mysql+pymysql://USUARIO:SENHA_CODIFICADA@HOST:3306/BANCO?charset=utf8mb4
MYSQL_SSL_CA=/caminho/para/ca-confiavel.pem
```

Os nomes em maiúsculas são campos a substituir, não credenciais funcionais. A senha deve estar percent-encoded se contiver caracteres especiais. `.env` é ignorado pelo Git. Sem uma URL MySQL válida o servidor não inicia; não há fallback local. MYSQL_SSL_CA configura validação do certificado e hostname do servidor. Se a conexão for por TLS, use a CA fornecida pelo operador; não desative verificações.

O endereço precisa ser acessível a partir do contêiner, e não apenas do computador. `localhost` dentro do contêiner é o próprio contêiner. Autorize o destino na rede do ambiente quando necessário. Não exponha o MySQL livremente na Internet.

## Executar

Instale Python 3.12, crie venv e instale `requirements-dev.txt` como descrito no README. Configure `.env` antes da execução:

```bash
python scripts/dev.py --setup
```

O script aplica Alembic e inicia a API. Ele precisa de credenciais que permitam DDL durante a migração. Para separar responsabilidades: execute `python -m alembic upgrade head` com o usuário de migrações e inicie Uvicorn com usuário de runtime de privilégios mínimos. Não aplique migrações no banco real sem revisar/autorização operacional.

Com Docker:

```bash
docker compose up --build -d --wait
```

Compose inicia somente API e Redis. DATABASE_URL aponta para seu servidor externo. Em produção, use uma etapa de migração controlada separada do runtime. Se a CA estiver no host, monte-a somente para leitura no contêiner e ajuste MYSQL_SSL_CA para o caminho interno; o arquivo não vai na imagem. Desenvolvimento sem TLS só é aceitável em rede confiável com política expressa do operador.

## Migrações e auditoria

A nova revisão cria triggers de auditoria MySQL e comparação de subject sensível a maiúsculas. A criação de triggers com binary logging pode exigir execução pelo DBA ou configuração aprovada de log_bin_trust_function_creators. A CI usa root apenas no serviço descartável, não na aplicação. Não conceda ao usuário da API TRIGGER, ALTER, DROP ou TRUNCATE: triggers não protegem contra administradores ou DDL. Datas usam UTC. Uma URL MySQL não converte automaticamente um banco de outro mecanismo; preservar backups e planejar conversão separadamente. Volumes antigos não são apagados por esta mudança.

## Testes

Use um banco MySQL vazio, descartável, cujo nome comece com `prontuario_test`. Configure MYSQL_TEST_URL de forma segura, confirme a limpeza com MYSQL_TEST_ALLOW_RESET igual ao nome do banco descartável e execute `python -m pytest -q`. **Os testes apagam as tabelas técnicas desse banco entre casos. Nunca aponte MYSQL_TEST_URL ao banco de aplicação.** Não há sementes ou dados de demonstração na aplicação; entradas de teste ficam somente no banco isolado.

Sem MYSQL_TEST_URL, os testes que precisam de banco são explicitamente pulados; os demais continuam disponíveis. A CI inicia MySQL exclusivo do runner. O Compose de aplicação não usa esse serviço.

## Backup remoto e recuperação isolada

`backup.py` agora usa cliente MySQL 8.4 em contêiner, conectando-se ao DATABASE_URL externo, sem servidor local. Requer Docker, rede até o servidor e conta de backup com privilégios adequados. A verificação precisa também de CREATE/DROP em banco temporário; não dê esses privilégios à conta da API.

```bash
mkdir -p backups
python scripts/backup.py keygen --key-file backups/storage.fernet
python scripts/backup.py backup --key-file backups/storage.fernet --file backups/database.backup.enc
python scripts/backup.py verify --key-file backups/storage.fernet --file backups/database.backup.enc
```

A senha é passada por arquivo temporário privado montado somente para leitura, sem argumento de linha de comando. A CA é montada quando MYSQL_SSL_CA está configurada. O dump é transacional para tabelas InnoDB e não deve ocorrer durante mudanças de schema. A restauração ocorre em banco `restore_check_...` novo, removido ao final; não sobrescreve o banco configurado. Backup é criptografado; guarde a chave em local separado. O script processa o dump em memória; grandes bancos precisam de solução operacional com streaming e política de retenção/recuperação.

## Certificado MySQL no Compose

Para desenvolvimento com TLS e CA fornecida pelo operador, adicione em `.env` **o caminho absoluto do arquivo no host**:

```dotenv
MYSQL_SSL_CA_HOST=/caminho/absoluto/ca-mysql.pem
```

No modo Python local, `MYSQL_SSL_CA` continua apontando ao arquivo legível no host. No Docker, o override fornece o caminho interno automaticamente:

```bash
docker compose -f compose.yaml -f compose.tls.yaml config --quiet
docker compose -f compose.yaml -f compose.tls.yaml up --build -d --wait
docker compose -f compose.yaml -f compose.tls.yaml ps
```

O arquivo é montado somente para leitura em `/run/mysql-ca.pem`. Use os mesmos dois `-f` nos comandos de logs, recriação e encerramento deste modo. O hostname em DATABASE_URL precisa corresponder ao certificado do servidor. O conteúdo da CA não é uma senha, mas não deve ser incorporado à imagem específica de cada desenvolvedor.

Em ambiente de build com proxy, construa primeiro com `--secret id=proxy_ca,...` conforme o README e use `up -d --no-build --wait` com os dois arquivos Compose. O segredo de build e o certificado MySQL são independentes.

## Atualização de segurança da identidade e TLS

A revisão 0003 usa `utf8mb4_0900_bin` (NO PAD) nos subjects OIDC. Ela preserva diferenças de caixa e espaços finais; não normalizar, aparar ou reaproveitar esses identificadores. Models e migração usam a mesma collation. Uma reversão à collation antiga pode falhar se subjects agora distintos colidirem; não remover registros para forçar o downgrade.

Com `APP_ENV=production`, MYSQL_SSL_CA deve indicar uma CA confiável existente e Redis deve usar `rediss://` com verificação de certificado e hostname. Redis pode usar REDIS_SSL_CA para CA privada; sem isso usa a confiança padrão do sistema. URLs não podem desabilitar TLS ou sobrescrever os timeouts por parâmetros. Em desenvolvimento o Compose continua usando Redis privado sem TLS. Não usar esse Compose como implantação de produção.
