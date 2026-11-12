# ADR 0009 — Administrador da aplicação com Keycloak de desenvolvimento

Atualização de 12/11/2026: as decisões de autenticação abaixo são históricas e foram substituídas pelo [login local da ADR 0010](0010-autenticacao-local.md). A configuração atual está em `backend/AUTHENTICATION.md`.

Status: autorizado pelo responsável, que escolheu Keycloak no Docker de desenvolvimento e solicitou o administrador dos usuários do sistema de prontuários.

O modo explícito `auth_dev.py up --with-backend` prepara o provedor e cria `admin` em `cadastro__usuarios`, com perfil `ADMINISTRADOR`, permissão `USUARIO_GERENCIAR`, vínculo ativo e auditoria. O login é do Keycloak; as permissões são verificadas no MySQL da aplicação, separadamente das credenciais de infraestrutura.

O UUID inicial é compartilhado entre o `sub` Keycloak e o `id` do cadastro (`provedor=keycloak`). O token passa por assinatura, emissor e audiência antes desse vínculo. Uma tabela geral de identidades externas permanece alternativa para múltiplos provedores e subjects não UUID. A integração atual não migra identidades nem introduz login local na API.

O bootstrap é explícito, transacional, recusa colisões e não reativa permissões revogadas. Senha aleatória e chaves TLS ficam fora do Git/build, com troca obrigatória da senha no primeiro acesso. As migrations não inserem cadastros. Nenhum paciente, profissional ou turma é criado; o administrador não ganha acesso clínico implícito.

Testes MySQL isolados verificam criação, idempotência, recusa de takeover, desativação/revogação e autorização HTTP. O setup verifica persistência dos arquivos privados e confiança TLS. O provedor real é validado separadamente. Veja o [roteiro operacional](../../backend/ADMINISTRADOR.md).
