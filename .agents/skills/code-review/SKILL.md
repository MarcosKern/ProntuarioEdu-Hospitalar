---
name: code-review
description: Review a Trello implementation card against its GitHub pull request, inspect test coverage and CI, request repository-member reviews, prepare and apply authorized fixes or conflict resolutions on the PR branch while preserving main, and report unresolved findings with an actionable checklist.
---

# Code review for Trello cards and pull requests

Use this skill when asked to review a Trello card implementation, a GitHub pull request linked to a card, or both. The intended task is to compare the card's current acceptance criteria with the PR implementation and move the work toward a verifiable outcome.

## Inputs and discovery

Identify the Trello card and pull request from the user's links, card activity, description, branch name, or repository search. Confirm the repository, PR number, source branch, base branch, and current head commit. If several cards or PRs plausibly match, inspect their links and activity before choosing. Ask only when the target remains ambiguous.

Read repository `AGENTS.md` files and the complete current card description, including checklist items, test instructions, dependencies, and recent comments. Treat the current card text as acceptance criteria. Do not assume checked checklist boxes prove implementation or passing tests.

Read the PR diff and relevant surrounding code, tests, schema/DDL, project conventions, and CI status at the current PR head. Compare the implementation criterion by criterion. Check for regressions caused by the PR's changes and verify that documentation and tests describe the same behavior.

## Review and test coverage

Report concrete findings with file paths and line numbers where available. Prioritize correctness, data integrity, authorization, privacy, transaction behavior, compatibility, and missing acceptance criteria. Distinguish blocking findings from non-blocking improvements.

Assess whether tests exercise the code changed by the PR. Prefer the project's documented test commands and isolated test services. For database integration tests, use only the approved disposable database and verify the configured database name and reset guard before running tests. Never point tests at an application or production database. Report passed, failed, skipped, and unexecuted tests accurately. A skipped integration test is not a pass.

Use coverage measurement when it is available without changing project dependencies. State the measured scope and percentage. Do not treat line coverage alone as proof that the card's behaviors are asserted. If a dependency must be installed temporarily for measurement, keep it out of tracked dependency files.

When the PR satisfies the card and relevant checks pass, submit an approving Codex review and record the evidence on the Trello card. If there are blocking gaps, request changes and publish a detailed summary with a checklist of exact changes and validation required. Do not approve while known blocking findings remain.

## Request reviews from repository members

Use GitHub's reviewer-request mechanism on the identified PR. Determine candidate reviewers from repository collaborators, CODEOWNERS, the card's assigned members, and existing PR context. Request a small, relevant set of available human reviewers, excluding the PR author and anyone already requested. If no suitable member can be identified or the integration cannot request them, state that limitation clearly.

Requesting human reviews does not count as receiving human approvals. Never merge unless repository policy is satisfied, including the required number of valid human approvals, completed Codex review, passing required checks, and any required architecture review. Do not use email, chat, or another messaging channel to solicit reviews unless the user explicitly asks for that channel.

## Conflicts and PR updates

Check mergeability against the latest base branch. When GitHub reports a conflict or uncertainty, independently reproduce the merge using Git or the repository's merge tooling without changing the base branch. Identify each conflicting path and inspect both sides plus the merge base.

Resolve conflicts by preserving all valid behavior from `main` and the PR. Treat `main` as authoritative for existing shared behavior, security controls, schemas, configuration, and tests. Do not resolve a conflict by blindly selecting one side or by deleting coverage. Combine changes where both are needed, keep the diff limited to the PR's scope, and run relevant conflict-resolution tests afterward.

When the user's request explicitly asks to resolve conflicts or update a specific PR, that request authorizes necessary commits and pushes to that PR's existing source branch. A request for review alone authorizes inspection and review publication, but does not authorize commits or pushes. This never authorizes pushing to, rewriting, or merging `main`, force-pushing, changing unrelated branches, or merging the PR. Respect stricter repository rules if present. If authorization for a particular destructive or history-rewriting operation is unclear, do not perform that operation.

After an authorized update, verify the new PR head, changed-file list, mergeability, CI results, reviewer requests, and resulting diff. Re-run relevant tests. Do not mark the Trello card complete until its acceptance criteria and validation are met. If the work cannot be completed safely, leave the PR unchanged and provide the unresolved findings and a precise checklist.

## Trello updates and final report

Post a concise review comment on the Trello card with the PR link, decision, test evidence, and outstanding actions. Move the card only when evidence supports the next workflow stage. A code-review approval with tests still pending moves to the test stage. A card reaches the completed list only after required tests pass and card criteria are satisfied.

Finish with a concise report that names the PR head reviewed, the review decision, human reviewers requested, tests and CI checked, any fixes or conflict resolution applied, Trello movement, and anything still blocking completion. Link directly to the PR and card.
