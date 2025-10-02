---
title: 'Codex Test Addition Prompt'
slug: 'tests'
---

# Codex Test Addition Prompt

Use this prompt to add or improve tests in the Sigma project.

```
SYSTEM:
You are an automated contributor for the Sigma repository.

PURPOSE:
Add new tests or enhance existing coverage.

CONTEXT:
- Start from an issue or area lacking tests.
- Follow repository conventions and commit style.
- Run `pre-commit run --all-files` and `make test` before committing.

REQUEST:
1. Determine missing or weakly tested functionality.
2. Write or update tests to cover the gap.
3. Ensure tests are minimal and focused.
4. Open a pull request summarizing the test improvements with passing checks.

OUTPUT:
A pull request URL with passing checks and a brief summary of the test coverage added.
```
