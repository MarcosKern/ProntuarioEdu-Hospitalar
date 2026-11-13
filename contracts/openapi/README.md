# Contrato OpenAPI

A fonte de verdade atual são as rotas FastAPI e os DTOs em [`backend/src/prontuario_backend`](../../backend/src/prontuario_backend). Em desenvolvimento/testes, a API publica o contrato em `/openapi.json` e o Swagger em `/docs`. Ambos ficam desabilitados em `APP_ENV=production`.

O contrato já descreve oito operações: saúde, login, identidade, validade da sessão, identidade administrativa, renovação, logout e troca de senha. A autenticação usa o formulário de senha da própria API e JWT; clientes compartilham HTTP/JSON, sem importar Models de persistência.

## Consultar ou exportar

1. Inicie a API seguindo o [README do backend](../../backend/README.md), usando banco autorizado e configuração válida.
2. Abra `/openapi.json` no mesmo endereço usado para acessar `/docs`.
3. No Postman, escolha **Import → Link** e informe esse endereço. Em Codespaces com porta privada, o cliente também precisa conseguir autenticar o túnel GitHub; se necessário, importe o arquivo exportado no terminal remoto.

Para exportar, execute de `backend` com a API local na porta 8000 (ajuste a URL se usa outra porta):

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path
from urllib.request import urlopen

with urlopen('http://127.0.0.1:8000/openapi.json', timeout=10) as response:
    schema = json.load(response)
output = Path('../contracts/openapi/openapi.json')
output.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + '\n')
print(output.resolve())
PY
```

A exportação consulta somente o schema público, sem obter tokens ou dados de usuários. `openapi.json` é um artefato gerado opcional: não editar manualmente nem mantê-lo como uma segunda especificação independente. Se for incluído em um PR, regenere-o após mudanças nas rotas/DTOs e revise a compatibilidade com os clientes.

## Conferir a compatibilidade

De `backend`, no terminal Linux/Codespaces:

```bash
env MYSQL_TEST_URL= MYSQL_TEST_ALLOW_RESET= .venv/bin/python -m pytest -q tests/contract
```

Os testes verificam operações, identificadores únicos, respostas, escopos, limites, headers de protocolo e referências do schema, sem conectar ao MySQL. Testes HTTP e integração continuam necessários para comprovar o comportamento real; o documento por si só não executa validações nem concede permissões.

Veja [CONTRATOS.md](../../backend/CONTRATOS.md), [autenticação](../../backend/AUTHENTICATION.md) e o [acompanhamento F01](../../backend/docs/F01.md).
