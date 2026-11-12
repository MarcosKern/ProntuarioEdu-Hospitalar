# Documentação e divisão de competências

- [Arquitetura](architecture.md): visão do fluxo e das dependências entre componentes.
- [Alternativas](architecture-options.md): opções, vantagens e critérios de escolha.
- [ADRs](adr/README.md): propostas e decisões arquiteturais com aprovação registrada.

Documentação de uma pasta explica responsabilidade, dependências e como desenvolver nela. ADR explica por que uma decisão foi escolhida. README principal orienta a navegação e o plano de desenvolvimento. Contratos descrevem a fronteira pública; não duplicar manualmente todas as suas definições aqui.

## Quem participa de uma mudança

| Competência | Responsabilidade |
| --- | --- |
| Produto e domínio | Definir regras reais, usuários e critérios de aceitação |
| Responsável pela arquitetura | Validar limites, decisões e impactos; registrar aprovação |
| Back-end | Regras, autorização no servidor, API e persistência |
| Desktop | Experiência Python e consumo correto da API |
| Web | Experiência responsiva, acessibilidade e consumo da API |
| Qualidade | Evidências de critérios de aceitação e comportamento nas fronteiras |
| Infraestrutura | Reprodutibilidade, implantação e recuperação |

São responsabilidades, não exigência de uma pessoa por papel. Uma mesma pessoa pode atuar em várias competências; mudanças de contrato e decisões precisam ser revisadas pelos componentes afetados. Nenhuma identidade de aprovador foi definida automaticamente.

Uma alteração funcional deve indicar o caso de uso, os componentes afetados, os contratos alterados, os testes necessários e se exige revisão da arquitetura. A organização MVC foi escolhida pelo responsável; FastAPI e MySQL externo já estão definidos; o login local JWT está definido na ADR 0010; tecnologias dos clientes e detalhes clínicos continuam pendentes. Exemplos documentais não aprovam funcionalidades clínicas nem substituem implementação.
