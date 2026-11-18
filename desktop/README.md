# Desktop Python

Proposta: cliente com separação entre apresentação, casos de uso locais e adaptadores. Toolkit gráfico ainda não escolhido.

- `src/prontuario_desktop/presentation`: telas e estado da interface.
- `src/prontuario_desktop/application`: coordenação dos fluxos do usuário e portas do cliente.
- `src/prontuario_desktop/adapters/api`: comunicação com a API pública versionada.
- `src/prontuario_desktop/bootstrap`: configuração e composição.
- `tests/unit`, `tests/integration`: testes de fluxos e comunicação.

O cliente não importa código interno do back-end nem acessa seu banco. Não armazenar segredos de aplicação no executável. Operação offline e persistência local dependem de decisão específica.

Ainda não há executável, toolkit ou dependências instaladas.

## Divisão de competências no desenvolvimento

| Parte | O que entrega | O que delega |
| --- | --- | --- |
| Apresentação | Layout, navegação, mensagens e estado visual | Fluxo para a aplicação local; rede para o adaptador |
| Aplicação | Coordenação de ações e porta de API | Regras autoritativas ao servidor; widgets à apresentação |
| Adaptador de API | Requisições HTTPS e tradução de respostas | Decisão de negócio ao Back-end |
| Bootstrap | Criação e conexão dos componentes | Comportamento às camadas próprias |

Exemplo: ao enviar uma anotação, a tela coleta o texto; o fluxo local aciona a porta da API; o adaptador envia a requisição; o servidor valida e responde; a aplicação local entrega o estado de sucesso ou erro à tela. A interface deve permanecer utilizável enquanto aguarda a rede.

Para uma nova funcionalidade, alinhe primeiro o contrato com o Back-end, depois implemente o adaptador, o fluxo e a tela, com testes em cada fronteira. Não importe entidades ou modelos do servidor. Alterações de toolkit devem afetar principalmente apresentação/bootstrap, não os fluxos e o contrato HTTP. Offline e armazenamento local continuam pendentes de decisão.


## Validação prevista

`tests/unit` deve testar fluxos e estados com uma API substituta, incluindo sucesso, rede indisponível e permissão negada. `tests/integration` deve verificar o cliente HTTP contra servidor de teste e a ligação entre apresentação e fluxos; testes gráficos dependem do toolkit escolhido. Ainda não há suíte executável ou comando de instalação do Desktop.

O adaptador deve ter timeout e não repetir escritas cegamente. Não registre tokens ou dados sensíveis. Bootstrap compõe e encerra os recursos; o armazenamento da sessão depende de uma decisão segura para o sistema operacional. A apresentação não deve bloquear durante I/O.

Consulte o [contrato público](../contracts/README.md) antes de implementar uma integração.
