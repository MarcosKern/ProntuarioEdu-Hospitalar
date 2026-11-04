# Visão da arquitetura proposta

A decisão está registrada na [ADR 0001](adr/0001-arquitetura-inicial.md), ainda pendente de aprovação.

```mermaid
flowchart LR
    Web[Web responsiva] --> API[API HTTPS / OpenAPI]
    Desktop[Desktop Python] --> API
    Apps[Outros aplicativos] --> API
    subgraph Backend[Back-end Python]
        API --> Application[Casos de uso e portas]
        Application --> Domain[Domínio]
        Persistence[Adaptador de persistência] -. implementa portas .-> Application
        Integrations[Adaptadores externos] -. implementam portas .-> Application
    end
    Persistence --> DB[(Banco a definir)]
    Integrations --> External[Serviços externos]
```

As setas contínuas mostram comunicação ou dependência. Os adaptadores de saída implementam portas definidas pela aplicação; o domínio não importa os adaptadores. O bootstrap conecta implementações e casos de uso.

Consulte os READMEs de cada componente para responsabilidades e os [critérios de validação](architecture-options.md) antes de iniciar a implementação.
