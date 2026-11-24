# Contrato público e OpenAPI

As rotas e os DTOs FastAPI em [`backend/src/prontuario_backend`](../backend/src/prontuario_backend) são a fonte de verdade. A API publica `/openapi.json` e `/docs` em desenvolvimento/testes; ambos ficam desabilitados em produção. Clientes compartilham HTTP/JSON e não importam Models de persistência.

Para iniciar a API e autenticar no Swagger, use o [roteiro principal](../backend/README.md). Os contratos de campos, erros e paginação estão em [contratos HTTP](../backend/docs/CONTRATOS.md).

## Importar e exportar

No Postman, use **Import → Link** com o endereço da API seguido de `/openapi.json`. Em Codespaces com porta privada, o cliente precisa autenticar o túnel GitHub; se isso não estiver disponível, importe um arquivo exportado no terminal remoto.

Com a API ativa na porta 8000, execute de `backend` (adapte a URL se alterou a porta):

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path
from urllib.request import urlopen

with urlopen('http://127.0.0.1:8000/openapi.json', timeout=10) as response:
    schema = json.load(response)
output = Path('../contracts/openapi/openapi.json')
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + '\n')
print(output.resolve())
PY
```

O JSON exportado é um artefato opcional, sem tokens ou dados de usuários. Não o edite manualmente como especificação paralela. Se incluído em um PR, regenere após alterações de rotas/DTOs e revise compatibilidade. `openapi/` fica reservado às exportações; `examples/`, a exemplos públicos sintéticos. Não inclua dados reais, senhas ou tokens válidos.

## Mudar uma operação

1. Combine entrada, saída, erros, escopos e critérios de aceite com os clientes.
2. Atualize implementação/DTOs e gere o OpenAPI pela própria API.
3. Execute os [testes de contrato](../backend/tests/README.md#verificações-sem-mysql) e os de integração pertinentes.
4. Revise mudanças incompatíveis e a estratégia de atualização dos clientes, inclusive versões Desktop já distribuídas.

O backend implementa as regras; Desktop e Web revisam o consumo; testes verificam concordância. Swagger apresenta o contrato e executa chamadas reais, mas não implementa as regras por si só.
