# ADR 0010 — Login local na API com MySQL e JWT

Status: aprovado pelo responsável em 12/11/2026, ao pedir a remoção do Keycloak e escolher explicitamente “Login na própria API com usuário/senha no MySQL e JWT”. Substitui a ADR 0009 e as decisões de provedor externo nas ADRs 0002/0003 para a implementação atual.

A complexidade do servidor de identidade, banco adicional, realm e certificados dificultava o desenvolvimento. A API FastAPI passa a autenticar os usuários de `cadastro__usuarios`, usando os campos de senha/bloqueio existentes e as sessões de `cadastro__sessoes_usuario`. Não cria outro framework, camada de serviço ou dependência pip.

A senha recebe hash scrypt com salt (N=32768, r=8, p=3). A API assina JWT HS256 com segredo externo à versão do código, audiência/emissor fixados por configuração e duração de 15 minutos por padrão. Refresh tokens aleatórios ficam somente como hashes no banco e são rotacionados. Cada operação protegida consulta a sessão, permitindo logout, troca de senha e bloqueios imediatos. A concessão administrativa continua no MySQL e não libera prontuários.

O Swagger utiliza o formulário OAuth2 de senha da própria API para desenvolvimento dos clientes próprios. Essa convenção não oferece OIDC/SSO nem concessão a terceiros. Alternativas consideradas: manter o provedor externo (rejeitada pelo responsável por complexidade) ou suspender o login (não escolhida).

O administrador é criado explicitamente por prompt, sem senha padrão ou arquivo de credencial. Contas externas existentes só são convertidas por `create_admin.py --convert-existing`, preservando ID e permissões e recusando reativação. Nenhum volume ou cadastro é apagado automaticamente. Recuperação de senha, MFA e integrações delegadas permanecem trabalho futuro.

Validação necessária: testes de assinatura/claims, senha/hash, login e revogação com MySQL isolado, Swagger/Codespaces e controles de transporte/rate limit. O scan da imagem da API permanece obrigatório; o Keycloak e sua cadeia Java são removidos do produto, não ignorados pelo scanner. Confira [autenticação](../../backend/AUTHENTICATION.md) e [administrador](../../backend/ADMINISTRADOR.md).
