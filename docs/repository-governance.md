# Governança solicitada

## Estado atual

As regras abaixo são requisitos do projeto. Ainda não foram aplicadas no GitHub: a tentativa de criação de ruleset retornou `Resource not accessible by integration` (HTTP 403). A leitura da API funciona, mas a integração não tem escrita administrativa. Este documento e `AGENTS.md` orientam o trabalho local, mas não bloqueiam ações no servidor.

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

Aplicar e testar os rulesets com acesso administrativo à API/interface do GitHub; habilitar a integração do Codex; definir responsáveis pela arquitetura e pela autorização de branches; implementar os checks; testar um PR permitido e casos bloqueados. Nenhuma dessas proteções deve ser declarada ativa até essa validação.

## Configuração concreta para o administrador

`github-ruleset.json` contém o ruleset de main/releases com quatro aprovações e bloqueio de exclusão/force push, sem bypass. Após conferir os requisitos e ter credencial administrativa adequada, aplicar da raiz com `gh api --method POST repos/MarcosKern/ProntuarioEdu-Hospitalar/rulesets --input docs/github-ruleset.json`. Conferir rulesets existentes antes para evitar duplicação. O arquivo não configura revisão do Codex nem check de arquitetura inexistente. O responsável mantém a configuração do code review conforme combinado. Nenhuma proteção remota foi declarada ativa.
