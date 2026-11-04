# Opções de arquitetura — decisão pendente

## Restrições conhecidas

Back-end e Desktop serão em Python. A Web terá interface responsiva para uso também em dispositivos móveis; sua tecnologia permanece em aberto. O back-end deve atender Web, Desktop e novas integrações. As opções abaixo são propostas, não uma decisão aprovada.

## Alternativas

| Opção | Organização | Quando usar | Custo principal |
| --- | --- | --- | --- |
| Monólito modular com arquitetura hexagonal | Um back-end Python, módulos de domínio e adaptadores para HTTP, banco e integrações | Início do projeto, equipe pequena ou média e regras de negócio em evolução | Exige disciplina para manter limites entre módulos |
| Django modular com API REST | Django + Django REST Framework, módulos de domínio e administração integrada | Cadastros, permissões, fluxos administrativos e necessidade de entrega rápida | Evitar acoplamento das regras de negócio a views e modelos |
| Microsserviços orientados a eventos | Serviços Python com APIs e eventos versionados | Domínios e equipes independentes, escala ou isolamento comprovadamente necessários | Operação, consistência distribuída, observabilidade e testes mais complexos |

As duas primeiras opções podem adotar os mesmos princípios hexagonais; Django/FastAPI são escolhas de framework, enquanto monólito/microsserviços são escolhas de distribuição. Não há necessidade de criar um back-end diferente para cada cliente.

## Recomendação para validação

Começar por um monólito modular Python, com regras de domínio independentes da interface e API REST versionada descrita por OpenAPI. Avaliar FastAPI para foco em API ou Django + DRF se administração, ORM e permissões integradas forem prioritários. PostgreSQL é uma opção de persistência a validar. Evitar escolher simultaneamente os dois frameworks sem necessidade concreta.

Web responsiva, Desktop Python e futuros aplicativos acessam a mesma API por HTTPS; somente o back-end acessa o banco. Clientes não são fontes confiáveis para autorização ou regras de negócio. PySide6/Qt é uma opção para Desktop, sujeita à validação de distribuição e licenciamento. A escolha da Web fica aberta, incluindo a avaliação futura de PWA.

REST atende operações usuais. Adicionar WebSocket ou SSE somente se houver necessidade de atualização em tempo real. Usar filas e workers para tarefas demoradas quando surgirem requisitos concretos. Um gateway ou BFF pode ser introduzido quando múltiplos serviços ou necessidades de cliente justificarem a camada.

## Critérios de aprovação da ADR inicial

- Definir módulos e seus limites, contratos OpenAPI e política de versionamento/compatibilidade.
- Escolher framework Python, persistência, migrações e estratégia de distribuição do Desktop.
- Definir autenticação; considerar OIDC/OAuth2 com Authorization Code + PKCE para clientes públicos e sessão segura para Web. Não embutir segredos de aplicação no Desktop ou no navegador.
- Definir autorização no servidor, isolamento de dados, auditoria, backups e restauração, retenção e proteção de dados sensíveis conforme o escopo real do prontuário.
- Decidir se o Desktop precisa funcionar offline. Se sim, especificar armazenamento local protegido, sincronização, conflitos e revogação de acesso; isso altera significativamente a arquitetura.
- Especificar testes de domínio, integração da API com banco, contratos e fluxos essenciais nos clientes.
- Registrar alternativas rejeitadas, riscos, responsáveis e aprovação explícita antes de iniciar a implementação.

Não foram instalados frameworks nem criados componentes de aplicação: a escolha arquitetural ainda depende dessa aprovação.
