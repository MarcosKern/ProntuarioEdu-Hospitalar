# ADR 0011 — Busca literal no catálogo de medicamentos

Status: aprovada pelo responsável em 24/11/2026. Esta decisão descreve o comportamento da busca por nome no Model do catálogo e não autoriza dados clínicos nem novas regras assistenciais.

## Contexto

O catálogo contém medicamentos ativos em `assistencial__medicamentos`. A consulta precisa localizar substrings pelo nome e ainda permitir paginação limitada. Os nomes podem conter caracteres que têm significado especial em padrões SQL, como `%` e `_`.

A implementação atual usa SQLAlchemy síncrono e SQL parametrizado no Model, conforme a organização MVC da [ADR 0001](0001-arquitetura-inicial.md). O banco permanece o MySQL 8.4 escolhido pelas ADRs anteriores.

## Decisão

A busca por nome trata o valor informado como uma substring literal:

- os caracteres `%`, `_` e `!` são escapados antes da montagem do padrão;
- o caractere `!` é declarado como escapador do operador `LIKE`;
- o termo é vinculado como parâmetro do SQL, não concatenado ao texto da consulta;
- o comparador `LIKE` procura ocorrências independentes de maiúsculas/minúsculas conforme a collation configurada no MySQL;
- a ordenação usa `nome, id` para desempate determinístico;
- a paginação continua limitada a `limite` entre 1 e 100 e `deslocamento` entre 0 e 100000.

Exemplos:

| Entrada | Resultado esperado |
| --- | --- |
| `%` | Encontra nomes que contêm o caractere percentual literal |
| `_` | Encontra nomes que contêm o caractere sublinhado literal |
| `!` | Encontra nomes que contêm o caractere de escape literal |
| `dipirona` | Encontra nomes que contêm essa substring |

A implementação não interpreta `%` ou `_` como curingas fornecidos pelo usuário. Essa escolha evita que uma entrada ampla altere indevidamente o resultado da busca.

## Alternativas

### Passar o termo diretamente ao `LIKE`

Rejeitada. Um usuário poderia usar `%` ou `_` como curingas do SQL e ampliar a pesquisa além do texto solicitado. Além disso, a regra ficaria menos previsível para nomes reais.

### Remover `%` e `_` da entrada

Rejeitada. Isso impediria que nomes legítimos fossem encontrados e transformaria o conteúdo da busca silenciosamente.

### Usar busca por termos de texto completo

Mantida como possibilidade futura. Full-text, stemming, sinônimos e ranking exigiriam configuração e critérios de produto próprios. Nenhuma dessas capacidades foi aprovada ou implementada nesta decisão.

### Criar repositórios ou ORM completo para esta consulta

Rejeitada no estado atual. A estrutura simples já disponível no Model atende ao volume e à responsabilidade desta consulta sem introduzir uma nova camada, conforme a ADR 0001.

## Consequências

Os consumidores podem pesquisar por conteúdo literal sem conhecer a sintaxe interna do MySQL. A busca permanece limitada em custo e retorna resultados ordenados de forma previsível.

O caractere `!` também é literal quando aparece na entrada porque é escapado junto com os demais caracteres especiais. A implementação não realiza normalização fonética, correção ortográfica, decomposição acentuada ou ranking por relevância.

Consultas SQL continuam parametrizadas. Entradas inválidas de paginação são rejeitadas antes do acesso ao banco. Nenhuma integração adicional é necessária para esta decisão.

## Contrato e implementação

O nome é um filtro opcional de substring. O limite e o deslocamento devem ser declarados na entrada HTTP futura ou pelo consumidor interno, com os mesmos limites desta decisão.

A implementação responsável está em [medicamentos.py](../../backend/src/prontuario_backend/models/medicamentos.py). A documentação física do banco está em [arquitetura_mysql.md](../../backend/docs/database/arquitetura_mysql.md). O formato dos contratos HTTP está em [CONTRATOS.md](../../backend/docs/CONTRATOS.md).

Esta ADR não cria automaticamente uma rota HTTP, uma View Pydantic ou um endpoint paginado. Controller, View e autorização devem ser definidos e aprovados antes da exposição pública.

## Segurança e dados

As entradas são vinculadas como parâmetros; o SQL não recebe o termo como fragmento textual. As consultas permanecem no servidor e não expõem usuários, senhas, SQL ou exceções internas.

Não serão criados dados de demonstração ou clínicos por esta decisão. O catálogo não contém dose, posologia, estoque, alergias ou eventos de administração. Essas áreas continuam pendentes de regras próprias.

## Validação

A decisão deve ser coberta por:

- teste unitário confirmando rejeição de paginação inválida antes do acesso ao banco;
- teste de integração com MySQL isolado confirmando filtro por substring e paginação;
- teste de integração confirmando que `%`, `_` e `!` correspondem apenas aos caracteres literais;
- teste confirmando que o termo de busca é enviado como parâmetro vinculado e não como parte do texto SQL;
- teste do contrato HTTP, quando o endpoint público for implementado, confirmando limites, erros e resposta paginada.
