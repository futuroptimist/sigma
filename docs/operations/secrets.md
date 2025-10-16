# Secrets management

Sigma relies on environment variables for API keys and service credentials.

1. Copy `apps/firmware/include/config.secrets.example.h` to
   `apps/firmware/include/config.secrets.h` when you need to embed Wi-Fi or API
   tokens in firmware builds. Keep the real file untracked.
2. Host-side services read from a `.env` file. Start by copying the
   repository-level [`.env.example`](../../.env.example) or export variables
   directly in your shell.
3. CI never receives secrets. Jobs rely on mocked values in tests to avoid
   leaking credentials.

## Environment variables

Populate the following keys in `.env` (or export them) to run the host-side
audio pipeline end to end:

| Variable | Purpose |
| --- | --- |
| `SIGMA_DEFAULT_LLM` | Preferred endpoint label from [`llms.txt`](../../llms.txt); blank uses the first entry. |
| `SIGMA_WHISPER_URL` | Base URL for the speech-to-text provider used by `sigma.whisper_client`. |
| `SIGMA_WHISPER_AUTH_TOKEN` | Authentication token injected into Whisper requests. |
| `SIGMA_WHISPER_AUTH_SCHEME` | Optional scheme prefix for the Whisper `Authorization` header (defaults to `Bearer`). |
| `SIGMA_LLM_URL` | Endpoint URL for the primary LLM provider. |
| `SIGMA_LLM_AUTH_TOKEN` | Authentication token for LLM queries. |
| `SIGMA_LLM_AUTH_SCHEME` | Optional scheme prefix for the LLM `Authorization` header (defaults to `Bearer`). |
| `SIGMA_AUDIO_DIR` | Directory where captured audio files are staged during tests. |

Whitespace is stripped from these values before use. When `SIGMA_WHISPER_URL`
is set but trims down to an empty string the speech-to-text helper raises a
`RuntimeError` so misconfiguration is detected immediately.

Use `scripts/scan-secrets.py` or `pre-commit run --all-files` before pushing to
ensure no tokens were accidentally committed.
