# Back-end Python

Proposta: monólito modular com arquitetura hexagonal. Framework e persistência dependem da ADR inicial.

- `src/prontuario_backend/domain`: entidades, objetos de valor e regras de negócio; sem imports de HTTP, banco ou interfaces gráficas.
- `src/prontuario_backend/application`: casos de uso e portas de entrada/saída; depende do domínio.
- `src/prontuario_backend/adapters/inbound/http`: tradução de requisições da API para casos de uso.
- `src/prontuario_backend/adapters/outbound/persistence`: implementação das portas de persistência.
- `src/prontuario_backend/adapters/outbound/integrations`: implementação das portas de serviços externos.
- `src/prontuario_backend/bootstrap`: configuração e composição de dependências.
- `tests/unit`, `tests/integration`, `tests/contract`: locais reservados para as respectivas verificações.

Somente o back-end acessa o banco. Autorização e regras de negócio são verificadas no servidor. Novos módulos de domínio devem ser definidos pelos requisitos, sem antecipar funcionalidades clínicas.

Ainda não há aplicação executável, dependências ou testes implementados.
