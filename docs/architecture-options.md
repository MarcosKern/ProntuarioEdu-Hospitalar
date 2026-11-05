# Arquitetura escolhida e ferramentas pendentes

A organização escolhida pelo responsável é **MVC no Back-end Python**, priorizando compreensão por uma turma intermediária. Não há mais proposta de organização hexagonal a implementar.

| Escolha | Situação |
| --- | --- |
| Models, Views e Controllers | Escolhido para organizar o servidor |
| Um Back-end compartilhado por todos os clientes | Mantido |
| Python no Back-end e Desktop | Mantido |
| Framework HTTP e persistência | FastAPI e SQLAlchemy/MySQL para desenvolvimento; ver ADR 0002 |
| Web responsiva e tecnologia Web | Responsividade obrigatória; tecnologia em aberto |

FastAPI foi adotado no ambiente inicial com Swagger integrado. Django + DRF oferece ORM, migrações e administração. Django usa a nomenclatura MTV: sua view costuma exercer o papel de Controller. Se for escolhido, registrar como as competências MVC mapeiam para suas convenções, sem duplicar classes apenas para manter nomes. A View conceitual da API corresponde à representação/serialização JSON.

MVC não é uma escolha de distribuição: o Back-end continua uma aplicação única. Microsserviços e abstrações adicionais ficam fora do escopo atual. Detalhes, justificativa e decisões pendentes estão na [ADR 0001](adr/0001-arquitetura-inicial.md).

A [ADR 0002](adr/0002-ambiente-desenvolvimento.md) registra as escolhas do ambiente executável e os limites da autenticação externa.
