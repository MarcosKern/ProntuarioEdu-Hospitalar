# Governança do repositório

As regras do trabalho estão em [AGENTS.md](../AGENTS.md). Esta página explica a política solicitada; o estado efetivo das proteções deve ser conferido em **GitHub → Settings → Rules → Rulesets** e nos checks do PR. Documentação não ativa uma proteção por si só.

## Branches e publicação

- Criar uma branch de trabalho é permitido.
- Commits, pushes, rebase/reescrita, alteração ou exclusão de branches existentes exigem autorização do responsável para a operação. Uma autorização já dada continua válida no seu escopo.
- Não use force push nem bypass de revisão como forma de resolver rejeição de atualização. Confira as alterações remotas e preserve o trabalho existente.
- Mantenha segredos, bancos, backups e arquivos de configuração privados fora do Git.

## Condições para merge

| Controle | Política |
| --- | --- |
| Entrega | Alterações por pull request |
| Aprovações humanas | Pelo menos quatro aprovações válidas |
| Revisão automática | Codex concluído; não substitui as aprovações humanas |
| CI | Testes, lint, auditoria de dependências, build/scan da imagem e CodeQL aplicáveis aprovados |
| Bloqueios | Discussões e achados de segurança resolvidos |
| Arquitetura | Decisão aplicável e sua validação aprovadas |

O projeto solicita revisão do Codex; Copilot não faz parte da política de revisão automática escolhida. Verifique as integrações e os nomes dos checks disponíveis no próprio GitHub antes de alterar um ruleset. Não remova checks para obter um PR verde.

O escopo de regras de merge e o de proteção contra exclusão/reescrita podem ser diferentes. Confira as branches abrangidas e o efeito das permissões de bypass com o administrador; não configure exceção permanente que dispense as aprovações exigidas.

## Alterações arquiteturais

MVC, FastAPI/MySQL e login local JWT têm decisões registradas nas [ADRs](adr/README.md). Mudanças de arquitetura e novas dependências de aplicação precisam registrar alternativas, justificativa, impacto e testes, além da aprovação explícita aplicável. A mera presença de um arquivo ADR não comprova uma aprovação.

Um gate automático de arquitetura exige responsáveis e evidência verificável de aprovação definidos pelo projeto. Não trate esse gate como implementado apenas por existir um README ou CODEOWNERS.

## Manter as regras no GitHub

Revise o ruleset existente antes de atualizá-lo; não crie outro duplicado. Use o painel do GitHub ou uma exportação atual revisada pelo administrador, preservando proteções e integrações aplicáveis. Identificadores de ruleset e resultados de execução mudam e não devem ser copiados de registros históricos como configuração vigente.
