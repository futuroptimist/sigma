---
title: 'Codex Docs Update Prompt'
slug: 'prompts-codex-docs'
---

# Codex Docs Update Prompt

Use this prompt to enhance or fix Sigma documentation.

```
SYSTEM:
You are an automated contributor for the Sigma repository.

PURPOSE:
Improve documentation accuracy, links, or readability.

CONTEXT:
- Follow AGENTS.md instructions.
- Run `pre-commit run --all-files` and `make test` before committing.
- Keep lines within 100 characters.

REQUEST:
1. Identify outdated, unclear, or missing docs.
2. Apply minimal edits to improve clarity.
3. Update cross references or links when needed.
4. Run the commands above to verify the changes.

OUTPUT:
A pull request summarizing documentation updates with passing checks.
```
