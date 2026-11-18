# Web responsiva

Tecnologia em aberto. A interface deve funcionar em desktop e dispositivos móveis e consumir a mesma API pública do Desktop.

- `src`: reservado até a escolha da tecnologia e de sua organização nativa.
- `tests`: testes futuros de comportamento, integração e acessibilidade.

Não há framework, gerenciador de pacotes, manifesto ou build definido. A decisão futura deve considerar responsividade, acessibilidade, autenticação, manutenção e eventual PWA. Não importar módulos Python internos do servidor nem acessar diretamente seu banco.

## Divisão de competências no desenvolvimento

| Responsabilidade conceitual | Conteúdo | Limite |
| --- | --- | --- |
| Apresentação | Componentes, páginas, formulários, navegação e acessibilidade | Não contém acesso direto ao banco ou segredos do servidor |
| Coordenação dos fluxos | Carregamento, erros, sessão e ações do usuário | Não é fonte autoritativa de permissões ou regras clínicas |
| Comunicação com API | Transporte, esquemas públicos e tradução dos erros | Não usa modelos internos do Back-end |
| Configuração | URL pública da API e composição das ferramentas escolhidas | Variáveis enviadas ao navegador não são secretas |

Essas são competências, não nomes de diretórios impostos. Depois de escolher o framework, documente como suas convenções representam cada responsabilidade; mantenha `src/` reservado até lá.

Para desenvolver um fluxo: revisar contrato e estados de erro, implementar comunicação, montar a experiência visual e verificar o comportamento em computador e celular. Testar teclado, toque, foco, leitores de tela e estados de rede. Esconder um botão não protege uma operação: o servidor deve negar acessos indevidos. Cache de dados sensíveis, PWA e offline exigem decisões explícitas.


Os testes futuros devem cobrir componentes/fluxos isolados, integração HTTP e acessibilidade. Inclua estados de carregamento, sessão expirada, permissão negada e falha de rede. Não há comando de build ou de testes até a escolha da tecnologia. O [contrato público](../contracts/README.md) é compartilhado com o Desktop.
