# imagegen-configured

`imagegen-configured` is a thin wrapper around Codex's built-in `imagegen` skill.

Use it when you want the latest system `imagegen` behavior, prompts, model/API parameters, and transparent-image workflow, but the actual image API request must use the currently configured Codex provider `base_url` and API key.

## What It Does

- Reads the current Codex provider from `$CODEX_HOME/config.toml`.
- Resolves `base_url` from that provider, falling back to `OPENAI_BASE_URL`.
- Resolves the API key from provider config, provider env key, `$CODEX_HOME/auth.json`, or `OPENAI_API_KEY`.
- Injects those values as `OPENAI_BASE_URL` and `OPENAI_API_KEY`.
- Delegates to the latest system script at `$CODEX_HOME/skills/.system/imagegen/scripts/image_gen.py`.

## Why It Exists

The built-in `imagegen` skill may use Codex's built-in image tool by default. This wrapper keeps the system `imagegen` skill untouched and updateable while forcing live API calls through your configured provider endpoint.

## Usage

Use this skill in prompts:

```text
Use $imagegen-configured to generate an image ...
```

For direct CLI use:

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/imagegen-configured/scripts/image_gen_configured.py" generate \
  --prompt "A simple test image" \
  --out output/imagegen/test.png
```

Run `--dry-run` first to inspect payloads and credential resolution.

Image generation often takes 3 minutes or more, so keep waiting unless there is an explicit error, disconnect, or timeout.
