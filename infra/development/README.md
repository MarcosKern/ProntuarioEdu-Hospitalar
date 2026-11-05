# Infraestrutura de desenvolvimento

Os arquivos ativos são `backend/Dockerfile`, `backend/compose.yaml` e o override `backend/compose.tls.yaml`. Esta pasta ainda não possui scripts próprios. Não duplique esses arquivos aqui.

Siga o [guia do Back-end](../../backend/README.md#configurar-o-ambiente-de-desenvolvimento). Os dois caminhos são Python local ou Docker Compose, sempre com MySQL externo configurado. Compose inicia Redis; o modo local pode usar limitador em memória apenas para desenvolvimento. A aplicação não cria um banco MySQL nem contas automaticamente.

Antes de acrescentar infraestrutura, documente configuração, inicialização, readiness, encerramento e preservação dos dados. A saúde da API precisa incluir consulta SQL, não somente porta aberta. Ambiente restaurado não garante que processos ou conexões continuem ativos.
