# Secrets management

Sigma relies on environment variables for API keys and service credentials.

1. Copy `apps/firmware/include/config.secrets.example.h` to
   `apps/firmware/include/config.secrets.h` when you need to embed Wi-Fi or API
   tokens in firmware builds.  Keep the real file untracked.
2. Host-side services read from a `.env` file.  Start by copying `.env.example`
   (created in this change) or export variables directly in your shell.
3. CI never receives secrets.  Jobs rely on mocked values in tests to avoid
   leaking credentials.

Use `scripts/scan-secrets.py` or `pre-commit run --all-files` before pushing to
ensure no tokens were accidentally committed.
