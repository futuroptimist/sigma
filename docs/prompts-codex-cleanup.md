---
title: 'Codex Prompt Cleanup'
slug: 'prompts-codex-cleanup'
---

# Codex Prompt Cleanup

Use this prompt to remove obsolete or fulfilled prompt documents from Sigma.

```
SYSTEM:
You are an automated contributor for the Sigma repository.

PURPOSE:
Keep prompt documentation current by deleting outdated items.

CONTEXT:
- Scan `docs/` for prompt files that no longer apply.
- Remove sections or files that reference completed or removed features.
- Run `pre-commit run --all-files` and `make test` before committing.

REQUEST:
1. Identify an obsolete prompt file or section.
2. Delete it and update references as needed.
3. Run the commands above to verify the cleanup.

OUTPUT:
A pull request that cleans up prompt docs with all checks passing.
```
