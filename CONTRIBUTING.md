# Contributing

1. Fork and clone the repository.
2. Run `pre-commit run --all-files` and `make test` before committing.
3. Scan your staged changes for secrets before committing:

   ```bash
   git diff --cached | ./scripts/scan-secrets.py
   ```

4. Open a pull request describing your changes.
