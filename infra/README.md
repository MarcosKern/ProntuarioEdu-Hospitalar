# Infraestrutura

- `development`: futuras configurações de serviços locais.
- `deployment`: futuras configurações de implantação.

Não há banco, contêiner ou provedor selecionado. Segredos devem vir da configuração segura do ambiente e nunca do repositório. Não existem comandos de infraestrutura executáveis nesta etapa.

## Divisão de competências no desenvolvimento

`development/` torna o ambiente local reproduzível. `deployment/` descreve como entregar e operar versões aprovadas. O código de aplicação permanece em seus componentes; configuração operacional não deve redefinir regras de negócio.

Quem mantém infraestrutura cuida de serviços, configuração, isolamento, logs, backups e prontidão. Quem mantém cada aplicativo informa os recursos e configurações necessários e fornece verificações funcionais. A estratégia de migração precisa ser combinada com o Back-end, incluindo compatibilidade e recuperação em falhas.

Antes de adicionar configuração, registre qual decisão a justifica. Depois, valide em ambiente de teste: inicialização, requisição representativa, encerramento, repetibilidade e recuperação. Ainda não existem Dockerfiles, serviços ou scripts de implantação para executar.
