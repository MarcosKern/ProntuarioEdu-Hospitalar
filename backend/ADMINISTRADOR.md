# Primeiro administrador do ProntuarioEdu

O login **`admin`** pertence aos usuários da aplicação: fica em `cadastro__usuarios`, com perfil `ADMINISTRADOR` e permissão `USUARIO_GERENCIAR`. O Keycloak realiza o login. As credenciais do MySQL e da gestão do provedor são separadas.

## Criar e iniciar

De `backend`, com o venv preparado:

```bash
.venv/bin/python scripts/auth_dev.py up --with-backend
```

O comando prepara senhas aleatórias e certificados HTTPS em `.local/auth/`, sobe Keycloak e seu MySQL separado, inicia o modo MySQL de desenvolvimento e a API e cadastra transacionalmente o administrador na aplicação. Somente o volume de desenvolvimento vazio importa o SQL de domínio. O bootstrap não seleciona o `DATABASE_URL` externo para inserir o usuário.

As próximas execuções preservam as contas e as senhas. O bootstrap não reativa usuários/perfis/permissões revogados nem assume um cadastro `admin` com outro vínculo. As migrations continuam sem cadastros automáticos. Nenhum paciente, profissional ou turma é criado.

## Senha e primeiro acesso

Abra localmente **`.local/auth/admin-inicial.txt`**. O arquivo contém o login `admin` e sua senha temporária, possui permissão `600` e está ignorado pelo Git e Docker. A senha não é impressa pelo script.

1. No acesso local, importe a CA pública `.local/auth/certs/ca.crt` no gerenciamento de certificados do navegador/sistema. A API usa `OIDC_SSL_CA` para verificar o HTTPS; não desative a validação de certificado.
2. Abra **http://127.0.0.1:8000/docs**.
3. Clique em **Authorize** e marque `identity:read` e **`admin:access`**.
4. Entre com **`admin`** e a senha do arquivo. O primeiro acesso exige a troca dessa senha.
5. Execute **`GET /api/v1/admin/me`** para conferir o cadastro, perfil e permissão da aplicação.

O segundo escopo só é concedido pelo Keycloak ao papel `ADMINISTRADOR`. A API também verifica, no próprio banco, o usuário ativo, perfil não revogado e a permissão `USUARIO_GERENCIAR`. Um papel ou escopo no token não basta sozinho. A conta não ganha acesso clínico implícito.

Após a troca, a senha inicial deixa de funcionar. Reiniciar não restaura a senha antiga. Não publique a pasta `.local/auth`, que também guarda chaves TLS e configurações privadas.

`401` indica token ausente/inválido/expirado; `403`, cadastro ou autorização insuficiente; `503`, dependência indisponível. O CRUD completo de usuários e a gestão de turmas ainda exigem seus respectivos cards.

## Vínculo e arquivos

O UUID inicial é compartilhado entre o usuário Keycloak (`sub`) e `cadastro__usuarios.id`, com `provedor=keycloak`. O emissor e a audiência são verificados antes da consulta. Essa integração não migra identidades de outros provedores automaticamente; `profissional_id` permanece vazio para a conta técnica inicial.

- `compose.auth.yaml`: provedor e banco de identidades; não importa o schema clínico.
- `compose.auth.backend.yaml`: rede e CA confiável usadas pela API.
- `docker/keycloak/prontuarioedu-realm.json`: template público com referências a variáveis privadas, sem senhas reais.
- `models/users.py`: cadastro, vínculo, permissão e bootstrap transacional.
- `controllers/admin.py`: autorização administrativa antes da execução.

Os projetos Compose são `prontuario-auth` e `prontuario-auth-app`, com volumes próprios. O Keycloak ignora um realm já existente: editar o JSON não atualiza uma instalação em uso. Não apague volumes para aplicar alterações sem um procedimento revisado.

Para parar o provedor preservando seu banco:

```bash
.venv/bin/python scripts/auth_dev.py down
```

Para parar a aplicação preservando seus volumes:

```bash
docker compose --project-name prontuario-auth-app \
  --env-file .env.mysql --env-file .local/auth/compose.env \
  -f compose.yaml -f compose.mysql.yaml -f compose.auth.backend.yaml down
```

`setup` prepara somente os arquivos. `info` mostra endereços e caminhos, sem senhas. `up` sem `--with-backend` sobe apenas o provedor, sem cadastrar o usuário no banco da aplicação.

## Codespaces e limites

O script calcula as origens das portas 8000 e 8080 pelo nome do Codespace. Encaminhe ambas como privadas e abra a porta do login pelo navegador para autenticar o túnel do GitHub. Use o endereço do Swagger impresso pelo script. O fluxo completo atrás da autenticação privada do GitHub precisa ser validado no Codespace real; não torne portas públicas para contornar o controle.

Este é um provedor de desenvolvimento. Produção exige infraestrutura, certificados, MFA, recuperação e políticas próprias. O login na gestão do provedor não é a conta `admin` do ProntuarioEdu. Veja a [ADR 0009](../docs/adr/0009-administrador-aplicacao-keycloak.md).
