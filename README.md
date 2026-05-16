# imagegen-configured

`imagegen-configured` is a thin wrapper around Codex's built-in `imagegen` skill.

The built-in `imagegen` skill uses the official ChatGPT/OpenAI API URL by default. Use `imagegen-configured` when you want the latest system `imagegen` skill behavior, prompts, model/API parameters, and transparent-image workflow, but the actual image API request must use the currently configured Codex provider `base_url` and API key, including third-party OpenAI-compatible providers.

## What It Does

- Reads the current Codex provider from `$CODEX_HOME/config.toml`.
- Resolves `base_url` from that provider, falling back to `OPENAI_BASE_URL`.
- Resolves the API key from provider config, provider env key, `$CODEX_HOME/auth.json`, or `OPENAI_API_KEY`.
- Injects those values as `OPENAI_BASE_URL` and `OPENAI_API_KEY`.
- Delegates to the latest system script at `$CODEX_HOME/skills/.system/imagegen/scripts/image_gen.py`.

## Installation

Clone this repository into your Codex skills directory:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
git clone git@github.com:ywlcode/imagegen-configured.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/imagegen-configured"
```

Restart Codex after installing so the skill list is reloaded.

## Disable Built-In imagegen

The easiest way is through Codex:

1. Run `/skills` in Codex.
2. Choose `Enable/Disable Skills`.
3. Disable the built-in/system `imagegen` skill.
4. Keep `imagegen-configured` enabled.

## Usage

Use this skill in prompts:

```text
Use $imagegen-configured to generate an image ...
```

Image generation often takes 3 minutes or more, so keep waiting unless there is an explicit error, disconnect, or timeout.
