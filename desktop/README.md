# Desktop Python

Proposta: cliente com separação entre apresentação, casos de uso locais e adaptadores. Toolkit gráfico ainda não escolhido.

- `src/prontuario_desktop/presentation`: telas e estado da interface.
- `src/prontuario_desktop/application`: coordenação dos fluxos do usuário e portas do cliente.
- `src/prontuario_desktop/adapters/api`: comunicação com a API pública versionada.
- `src/prontuario_desktop/bootstrap`: configuração e composição.
- `tests/unit`, `tests/integration`: testes de fluxos e comunicação.

O cliente não importa código interno do back-end nem acessa seu banco. Não armazenar segredos de aplicação no executável. Operação offline e persistência local dependem de decisão específica.

Ainda não há executável, toolkit ou dependências instaladas.
