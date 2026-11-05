# Apresentação Desktop

## Responsabilidade

Telas, componentes, estado visual, mensagens e interação do usuário.

## Divisão de competências

Depende dos fluxos locais, não de bibliotecas HTTP. Não bloquear a interface durante I/O; escolher o mecanismo assíncrono compatível com o toolkit. Validar para orientar o usuário sem substituir a validação do servidor.

## Como desenvolver aqui

Defina primeiro a entrada, a saída e as dependências permitidas da alteração. Implemente apenas a responsabilidade desta pasta; mudanças em outras fronteiras devem atualizar seus contratos e testes. Consulte o README do componente e a ADR inicial antes de introduzir dependências.

Esta pasta faz parte de uma proposta documental. Ainda não há implementação nem comando de execução próprio.
