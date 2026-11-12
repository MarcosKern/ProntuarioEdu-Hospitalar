# Administrador da aplicação

O usuário `admin` pertence ao ProntuarioEdu e faz login na própria API. Sua senha é armazenada somente como hash scrypt no MySQL. O perfil `ADMINISTRADOR` e a permissão `USUARIO_GERENCIAR` continuam separados das contas de conexão ao banco.

## Preparar e criar

1. Prepare `.env` e `AUTH_JWT_SECRET` conforme [autenticação](AUTHENTICATION.md#configuração).
2. Inicie o [MySQL de desenvolvimento e a API](docker/mysql/README.md). Esse modo importa o SQL de domínio em volume vazio e aplica as migrations técnicas. Para MySQL externo, o responsável deve aplicar o schema de domínio antes deste cadastro; as migrations técnicas sozinhas não criam `cadastro__usuarios`.
3. No terminal de `backend`, use os mesmos arquivos Compose do ambiente iniciado:

```bash
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml \
  exec backend python scripts/create_admin.py
```

O comando pede a senha duas vezes, sem exibi-la. Use de 12 a 128 caracteres e guarde-a no seu gerenciador de senhas. Não existe senha padrão nem arquivo `admin-inicial.txt`. A senha é enviada ao MySQL somente como hash com salt aleatório.

Para Python local, com `.env` apontando deliberadamente ao banco de desenvolvimento correto, execute `.venv/bin/python scripts/create_admin.py`. O comando altera o banco configurado nessa execução.

O cadastro cria usuário, perfil, permissão e auditoria em uma transação. Reexecutá-lo preserva a senha do admin local existente; não reativa usuários nem refaz concessões revogadas. Não há pacientes ou contas de demonstração automáticas.

## Se já havia administrador externo

A conversão é explícita e preserva o ID e as concessões existentes:

```bash
docker compose --env-file .env.mysql -f compose.yaml -f compose.mysql.yaml \
  exec backend python scripts/create_admin.py --convert-existing
```

Defina uma nova senha local no prompt. A conversão recusa conta inativa ou sem concessão administrativa, sem restaurar permissões. A senha anterior do provedor externo deixa de autenticar esta aplicação. Nenhum volume é apagado.

Se seu ambiente antigo usa outro nome de projeto Compose, informe o mesmo `--project-name` usado na criação, por exemplo `prontuario-auth-app`; isso preserva o MySQL desse projeto. Após atualizar o código, recrie somente o serviço `backend` com os arquivos Compose atuais, sem os antigos overrides de identidade. Em `.env`, configure a chave JWT antes de recriar.

## Entrar e conferir

1. Abra `/docs`, na mesma porta da API: localmente, **http://127.0.0.1:8000/docs**.
2. Clique em **Authorize**, informe `admin` e sua senha; marque `identity:read` e `admin:access`. Deixe client ID e client secret vazios caso a interface os exiba.
3. Execute `GET /api/v1/admin/me`. A API verifica JWT, sessão ativa, cadastro, perfil e permissão no banco.
4. Use `POST /api/v1/auth/password` para trocar a senha; a operação encerra todas as sessões e exige novo login.

`401` indica credencial/token/sessão inválida; `403`, permissão insuficiente; `503`, configuração ou banco indisponível. O administrador não ganha acesso clínico implícito.

## Serviços e configuração

A API e o MySQL fazem a autenticação. Redis continua sendo usado pelo limitador HTTP do Compose existente. Não é necessário servidor de identidade, segundo MySQL, realm, CA própria de login ou cofre adicional. No Codespace, basta a porta da API como privada e seu hostname exato em `ALLOWED_HOSTS`.

Os arquivos privados de uma instalação antiga não são reutilizados. Após validar o login local, remova suas cópias antigas de senhas e certificados com o responsável pelo ambiente. O banco e o volume da aplicação devem ser preservados. Veja [autenticação](AUTHENTICATION.md) e [ADR 0010](../docs/adr/0010-autenticacao-local.md).
