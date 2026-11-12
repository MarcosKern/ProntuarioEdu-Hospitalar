# Documentação do banco MySQL

Esta pasta incorpora as fontes Markdown e SQL recebidas do responsável, revisadas para **MySQL 8.4 externo com InnoDB**. Os arquivos são referências para revisão e desenvolvimento futuro. Sua inclusão não aplica o schema, não cria endpoints e não modifica a arquitetura MVC ou a autenticação local JWT atual.

## Por onde começar

1. Leia os limites e diferenças para a aplicação atual neste README.
2. Consulte o [modelo e dicionário de dados](arquitetura_mysql.md), com fluxos e regras de negócio propostas.
3. Confira os tipos, constraints, relacionamentos e índices no [SQL de referência](prontuarioedu_mysql.sql).
4. Use o [grafo Mermaid das FKs](diagramas/relacionamentos_mysql.mmd) para acompanhar dependências entre tabelas. As setas vão da tabela que contém a FK para a tabela referenciada.

Os PDFs anteriores não foram incluídos como se fossem versões atualizadas: a revisão editável foi feita a partir de `prontuarioedu_arquitetura.md` e `prontuarioedu_mysql.sql`. Referências a figuras e arquivos não fornecidos foram substituídas por um diagrama de visão geral e um grafo extraído do SQL.

## Organização do modelo

Há **um banco chamado `prontuarioedu`**, com seis domínios identificados por prefixos. Em MySQL, `SCHEMA` é sinônimo de database; os domínios abaixo não exigem seis databases.

| Domínio / prefixo | Tabelas | Responsabilidade |
| --- | ---: | --- |
| `cadastro__` | 19 | Identidade, perfis, turmas, grupos, pacientes, atendimentos e alocações |
| `assistencial__` | 11 | Contextos, medicamentos, prescrições, aprazamentos e administração |
| `clinico__` | 9 | Registros assistenciais, avaliações, dispositivos e balanço hídrico |
| `cirurgia_maternidade__` | 10 | Cirurgia, parto, checklists e avaliações neonatais |
| `cme__` | 12 | Materiais, kits, expurgo, estoque e esterilização |
| `auditoria__` | 3 | Eventos, autenticação e metadados de anexos |
| **Total** | **64** | **121 FKs, 40 CHECKs e 30 índices auxiliares explícitos** |

PKs, índices de UNIQUEs declaradas nas tabelas e índices criados pelo MySQL para apoiar FKs são adicionais aos 30 `CREATE INDEX` explícitos.

## O que foi revisado para MySQL

- O dicionário agora reproduz os nomes físicos e os `CREATE TABLE` do SQL MySQL, incluindo as colunas geradas. Cada entidade lista também suas FKs e índices auxiliares.
- Identificadores usam `CHAR(36)` com `ascii_bin`, números exatos usam `DECIMAL`, estruturas esparsas usam `JSON` e horários usam `DATETIME(6)`. UUIDs gerados com `UUID()` não exigem extensões. O tipo `CHAR(36)` por si só não valida o formato de um UUID.
- Horários devem ser gravados em UTC pela aplicação. O DDL configura sua sessão com `SET time_zone = '+00:00'`; `DATETIME` não realiza conversão automática de fuso.
- A organização usa `dominio__tabela` no mesmo database e FKs InnoDB entre essas tabelas. Nomes físicos não devem ser substituídos por `dominio.tabela` em consultas ou Models MySQL.
- Unicidades condicionais usam índices UNIQUE sobre colunas geradas que retornam `1` ou `NULL`. Por exemplo, `chave_atual` diferencia ocupações abertas das encerradas. Regras que dependem do relógio, como expiração de alocação, continuam exigindo verificação na consulta e transação.
- A largura de exibição obsoleta `TINYINT(1)` foi substituída por `TINYINT`, sem mudar armazenamento, defaults, expressão gerada ou constraints. Flags continuam exigindo validação explícita de 0/1 quando essa regra for necessária.
- UUIDs e hashes com collation explícita preservam comparação binária. O login usa `utf8mb4_0900_as_ci`; o restante mantém a collation fornecida. A autenticação atual usa `cadastro__usuarios` com `provedor=local` e senha em hash scrypt, além de `cadastro__sessoes_usuario`, conforme a [ADR 0010](../../../docs/adr/0010-autenticacao-local.md).
- As referências a políticas nativas de autorização por linha foram substituídas pela validação por objeto no backend. FKs e CHECKs não verificam o usuário autenticado nem concedem permissão de leitura.

O projeto das tabelas recebido foi preservado. O perfil administrativo inicial e sua permissão de gestão de usuários já são usados pelo bootstrap explícito. As demais regras educacionais, fórmulas clínicas, perfis e invariantes entre registros continuam como propostas de domínio a validar; documentá-las não significa implementá-las ou homologá-las.

## Diferença para o backend que já funciona

As migrações em [`../../migrations`](../../migrations) mantêm as tabelas técnicas `record_permissions` e `audit_events`, além do controle `alembic_version`. Elas **não criam as 64 tabelas deste documento**. As tabelas técnicas e o domínio recebido têm finalidades e nomes diferentes; não devem ser renomeados ou unidos automaticamente.

A aplicação já utiliza senha local com hash e sessões para autenticação JWT. Recuperação de acesso e MFA continuam pendentes, apesar de suas tabelas existirem. O [administrador inicial](../../ADMINISTRADOR.md) é criado explicitamente em `cadastro__usuarios`, com perfil `ADMINISTRADOR` e `USUARIO_GERENCIAR`; contas externas só são convertidas por comando explícito.

Não há INSERTs, usuários padrão ou pacientes de demonstração no SQL. A coluna `ficticio` faz parte da modelagem educacional recebida; sua presença e seu default não inserem pacientes. Os cenários ilustrativos da documentação não são scripts de carga.

O cadastro do administrador é posterior à criação do schema: execute `scripts/create_admin.py` na própria API, usando sua conexão configurada. A senha é digitada no terminal e somente seu hash é enviado ao banco. O comando não cria tabelas, pacientes nem reativa concessões revogadas.

## Aplicação do schema

O responsável autorizou a inicialização deste SQL no [modo opcional MySQL em contêiner de desenvolvimento](../../docker/mysql/README.md). Esse caminho embarca o arquivo na imagem e executa a criação do banco e das tabelas no primeiro uso de um volume vazio. A criação das tabelas não implementa automaticamente os fluxos de negócio. O vínculo administrativo inicial já está integrado separadamente; para o servidor externo e os demais módulos de domínio, as etapas abaixo continuam necessárias.

O arquivo SQL contém `CREATE DATABASE IF NOT EXISTS prontuarioedu` e `USE prontuarioedu`. **Selecionar outro banco na linha de comando não muda esse destino.** Não importe o arquivo no servidor real como parte da configuração do editor ou da API.

O DDL destina-se a uma instalação inicial em banco vazio; os `CREATE TABLE` não são idempotentes. No MySQL, DDL provoca commits implícitos: uma falha intermediária pode deixar parte da estrutura criada. Reexecutar o arquivo sem analisar esse estado pode falhar ou conflitar com objetos existentes.

Antes de expandir a integração de domínio ou aplicar o schema fora do modo de desenvolvimento autorizado, será necessário:

1. Validar o modelo com o responsável, incluindo autenticação, autorização, regras educacionais e nomes físicos.
2. Definir migrações Alembic por etapa, compatibilidade com as tabelas técnicas atuais e estratégia de implantação/recuperação.
3. Separar contas de migração e runtime, com privilégios mínimos, acesso de rede e TLS configurados conforme o [guia MySQL](../../MYSQL.md).
4. Implementar invariantes que dependem de outras linhas em transações adequadas: cadeia prescrição/checagem/administração, participação em grupos, ocupações históricas e concorrência de estoque.
5. Definir auditoria e retificação das tabelas de domínio. O DDL recebido não cria triggers append-only para essas tabelas; os triggers existentes da aplicação protegem apenas a auditoria técnica.
6. Executar testes de integridade, autorização, concorrência e restauração em um MySQL descartável separado, sem apontar a suíte ao banco de aplicação.

O Compose base, as migrações técnicas existentes e os hooks de Codespaces não importam o SQL. A importação automática ocorre somente ao iniciar explicitamente o modo MySQL de desenvolvimento com um volume vazio.

## Validação desta revisão

O dicionário, as tabelas do SQL e o grafo devem permanecer sincronizados: 64 nomes físicos únicos, 121 FKs, 40 CHECKs e 30 índices auxiliares. As 105 regras e os critérios de aceite do material foram preservados como referência, com os recursos físicos alinhados ao MySQL.

Nesta revisão, o SQL foi importado em um contêiner MySQL 8.4 descartável, sem rede. A importação terminou sem avisos: foram conferidas 64 tabelas InnoDB, 121 FKs, 40 CHECKs e zero registros de aplicação. O contêiner e seu armazenamento temporário foram removidos ao final; nenhum banco real foi acessado.

Essa validação estrutural do SQL não executou o bootstrap administrativo e não comprova os demais fluxos de negócio, políticas de acesso ou resultados clínicos. O cadastro e a autorização do administrador possuem testes próprios; a ampliação do uso real depende das etapas anteriores.
