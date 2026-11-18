# Hospedagem e operação

Os arquivos executáveis de contêiner ficam em `backend/`. Não existe outro Compose nesta pasta. O [roteiro principal](../backend/README.md) explica construção, inicialização, saúde, acesso ao Swagger, atualização e parada.

## Rodar em um servidor de desenvolvimento

1. No servidor Linux, instale Docker Engine/Compose e Python 3.12 conforme o roteiro principal. A conta operadora precisa de acesso autorizado ao daemon Docker.
2. Faça o checkout da branch desejada e execute o mesmo roteiro, mantendo arquivos privados e volume de banco nesse servidor.
3. A API fica publicada somente no loopback do servidor (`127.0.0.1:8000`); `-d` mantém os serviços em segundo plano enquanto o Docker estiver funcionando.
4. Para abrir o Swagger do seu computador, crie um túnel SSH autorizado:

```bash
ssh -L 8000:127.0.0.1:8000 usuario@servidor
```

Substitua usuário/servidor. Com o túnel aberto, acesse **http://127.0.0.1:8000/docs** no seu navegador. Se a porta local estiver ocupada, use `8001:127.0.0.1:8000` e abra a porta 8001. O túnel precisa permanecer ativo. Não é necessário abrir MySQL ou Redis para a Internet.

No Codespaces, o túnel é o encaminhamento privado da aba Ports, já explicado no roteiro principal; não use esse comando SSH ali.

## Implantação de produção

O Compose disponível tem reload e configurações de desenvolvimento. Não há implantação de produção automatizada pronta. `APP_ENV=production` desativa Swagger e `/openapi.json`; abrir a documentação não é um objetivo da publicação de produção.

Antes da entrega, definir domínio/HTTPS e gateway confiável, imagem imutável sem reload, política de reinício, rede privada, segredos, conta de migrations separada do runtime, MySQL/Redis com TLS, backups/recuperação e monitoramento. Os requisitos implementados e pendentes estão em [segurança](../backend/docs/SEGURANCA.md#produção-requisitos-ainda-externos). A escolha da hospedagem e suas configurações precisam de validação própria.
