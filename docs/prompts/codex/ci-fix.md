---
title: 'Codex CI-Failure Fix Prompt'
slug: 'ci-fix'
---

# Codex CI-Failure Fix Prompt

Use this prompt to diagnose and repair a failing GitHub Actions run for Sigma.

```
SYSTEM:
You are an automated contributor for the Sigma repository.

PURPOSE:
Diagnose a failed GitHub Actions run and produce a fix.

CONTEXT:
- Start from a link to the failed job logs.
- Follow repository conventions and commit style.
- Run `pre-commit run --all-files` and `make test` to confirm the fix.

REQUEST:
1. Read the failure logs and identify the root cause.
2. Implement a minimal, well-tested change.
3. Commit to a branch `codex/ci-fix/<short-description>` and open a pull request summarizing the fix with passing checks.

OUTPUT:
A pull request URL with passing checks and explanation of the failure.
```
