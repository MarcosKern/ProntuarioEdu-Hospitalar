# ADR 0001 — Back-end MVC e clientes separados

Status: escolha de MVC aprovada pela solicitação explícita do responsável para simplificar a estrutura. Frameworks e decisões técnicas listadas abaixo continuam pendentes.

## Contexto

A turma tem conhecimento intermediário e considerou a proposta anterior complexa. Foi solicitado substituir a organização hexagonal do Back-end por MVC e adaptar as pastas e a documentação. A proposta anterior não tinha implementação de aplicação.

## Decisão

Organizar o Back-end Python em Models (dados e regras), Controllers (coordenação e acesso) e Views (respostas JSON), com rotas e configuração de apoio. Um único servidor oferece API HTTPS compartilhada por Desktop Python, Web responsiva e novos aplicativos. Apenas o servidor acessa seu banco.

Remover as pastas documentais anteriores de domínio, aplicação, adaptadores e bootstrap do Back-end. O Desktop mantém sua organização de cliente já existente; não importa código do servidor. A tecnologia Web continua em aberto.

## Alternativas e consequências

A organização hexagonal foi substituída por aumentar o número de conceitos para o objetivo didático atual. Microsserviços não serão introduzidos. MVC facilita localizar responsabilidades, mas exige disciplina para não acumular regras nos Controllers nem serializar modelos inteiros nas Views. Models podem usar diretamente o ORM escolhido, sem interfaces de repositório obrigatórias.

MVC descreve organização interna; o servidor continua uma aplicação única. Não há necessidade de substituir frameworks para aplicar essa decisão, pois nenhum foi instalado.

## Contratos e segurança

Definir OpenAPI como contrato público, usando geração de esquema conforme o framework escolhido e Swagger UI para visualização. Controllers usam identidade autenticada e verificam acesso aos registros; Models validam regras; Views expõem apenas campos públicos. Autor, papel e permissão enviados pelo cliente não são prova de autorização. Definir transações, auditoria, proteção de dados e recuperação antes de produção.

## Testes

Unitários verificam regras dos Models, coordenação de Controllers e formatação de Views. Integração verifica API, autorização e persistência em ambiente isolado. Contrato verifica compatibilidade com OpenAPI. Testes ainda não implementados.

## Decisões pendentes

Framework Python, ORM/banco, autenticação, toolkit Desktop, tecnologia Web e necessidade de offline. A escolha de MVC não aprova uma funcionalidade clínica específica nem essas dependências. Mudanças futuras de arquitetura precisam de revisão e decisão registrada.
