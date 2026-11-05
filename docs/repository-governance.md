# Governança solicitada

## Estado atual

O ruleset Branch (26643855) está ativo. A leitura confirmou quatro aprovações, invalidação após push, aprovação do último push, resolução de conversas e checks test/image do GitHub Actions. Seu escopo atual é **todas as branches**, inclusive branches de trabalho.

A configuração remota também exige CodeQL/code_quality e contém novamente Copilot. A tentativa desta tarefa de remover somente Copilot recebeu HTTP 403 (`Resource not accessible by integration`). Nenhuma regra remota foi alterada. A revisão apenas pelo Codex continua sendo o requisito; a ativação própria do Codex e a configuração nativa de qualidade precisam ser conferidas pelo administrador.

O workflow CodeQL Python foi preparado no repositório para produzir a análise, sem remover o gate exigido. Default setup CodeQL não pôde ser consultado por falta de permissão. Se já estiver ativo, evitar duplicação com o workflow avançado. Preparar arquivo não comprova que o serviço executou ou que o merge está liberado.

## Proteção para merge

Configurar um ruleset ativo para `main` e futuras branches de release, sem bypass rotineiro:

1. Exigir pull request e no mínimo quatro aprovações humanas válidas.
2. Invalidar aprovações após novos commits e exigir aprovação do último push por outra pessoa.
3. Exigir resolução das conversas e checks obrigatórios aprovados.
4. Bloquear exclusão e force push.
5. Exigir os checks reais de arquitetura e revisão automática descritos abaixo, depois de implementar e validar suas integrações. Não cadastrar nomes de checks inexistentes como se já estivessem funcionando.

O repositório precisa de revisores elegíveis suficientes para alcançar quatro aprovações. A disponibilidade dos rulesets e de suas opções depende do plano e da visibilidade do repositório.

## Revisão automática pelo Codex

- Habilitar a integração de code review do Codex para este repositório e a revisão automática dos PRs nas configurações correspondentes.
- A revisão automática não substitui as quatro aprovações humanas exigidas.
- Implementar um check obrigatório que confirme que o Codex revisou o SHA atual do PR e que achados bloqueantes foram resolvidos. Definir os eventos, identidades e critérios reais após habilitar as integrações.
- O agregador deve falhar ou permanecer pendente quando uma revisão estiver ausente, desatualizada ou indisponível. Uma simples menção aos bots ou a existência de comentários não equivale a aprovação.
- Vincular checks obrigatórios à aplicação emissora esperada quando o GitHub permitir; não confiar apenas no nome do check.

A revisão automática deve usar apenas o Codex. Sua ativação ainda não foi confirmada; a criação de rulesets continua negada pela integração. Nenhuma integração nem check foi instalado neste onboarding.

## Autorização de branches

Criar branches é permitido. Excluir ou alterar branches existentes requer autorização explícita. O GitHub não fornece um pedido de autorização interativo para cada operação Git.

Para impor essa política no servidor, usar um ruleset aplicável às branches existentes, restringindo atualizações e exclusões a uma aplicação/fluxo de autorização controlado. A criação de branches deve permanecer liberada. Um bypass permanente para usuários permite operações sem autorização por operação e não satisfaz sozinho este requisito. O mecanismo deve permitir também os merges aprovados e evitar bloquear o fluxo de quatro revisões.

Até existir esse fluxo, `AGENTS.md` exige autorização dos agentes, mas não impede operações de usuários ou clientes Git externos. A política rigorosa também impede pushes de atualização de PRs sem autorização; qualquer exceção para branches de trabalho precisa ser decidida pelo responsável.

## Validação da arquitetura

A escolha de MVC foi autorizada pelo responsável e registrada na ADR 0001. Antes da primeira implementação, completar e aprovar as decisões de framework, contratos, autenticação, autorização, persistência e comportamento offline. Para mudanças posteriores, exigir ADR quando houver impacto arquitetural e justificativa revisada quando não houver.

Implementar um check obrigatório que valide a ADR aplicável e sua aprovação por responsáveis designados. A mera presença de um arquivo ADR não prova aprovação. O responsável, sua identidade no GitHub e a forma verificável de registrar aprovação ainda precisam ser definidos. Revisão por CODEOWNERS pode complementar o processo, mas não prova aprovação de uma pessoa específica em cada ADR sem validação adicional.

## Conclusão administrativa pendente

As regras de PR e os checks test/image estão ativos. Permanecem pendentes a remoção do Copilot, a verificação da revisão do Codex, a execução de CodeQL/qualidade e um gate verificável de aprovação arquitetural. A validação de autorização por operação de branch exige fluxo próprio; não é fornecida automaticamente pelo ruleset.

## Configuração concreta para o administrador

`github-ruleset.json` preserva todas as regras atualmente observadas e remove somente Copilot; não elimina CodeQL, code_quality ou as aprovações. Para atualizar o ruleset existente com credencial administrativa, conferir primeiro seu conteúdo atual e executar da raiz:

```bash
gh api --method PUT repos/MarcosKern/ProntuarioEdu-Hospitalar/rulesets/26643855 --input docs/github-ruleset.json
```

Não usar POST para essa atualização, pois criaria uma regra duplicada. O ruleset abrange todas as branches: validar o fluxo de atualização de PRs e decidir com o responsável se regras de merge devem ficar apenas em main/releases, mantendo exclusão/force push bloqueados para todas. Não criar bypass permanente que contorne as aprovações.

O arquivo não ativa o Codex nem implementa um gate de aprovação arquitetural. Essas integrações dependem de configuração e critérios verificáveis próprios. Não remover gates de segurança apenas para obter CI verde.
