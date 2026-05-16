---
name: "imagegen-configured"
description: "Wrapper around the system imagegen skill that generates or edits raster images through the currently configured Codex base_url and API key. Use when an image request should follow the latest built-in imagegen prompting/model/API guidance but the actual API call must go through the configured provider endpoint instead of the built-in image tool."
---

# Configured Imagegen Wrapper

This skill is a thin overlay on top of the system skill at `$CODEX_HOME/skills/.system/imagegen`.

Use this skill for the same raster-image tasks handled by the built-in `imagegen` skill: new image generation, image edits, variants from references, transparent-background assets, website/game/UI/product/mockup imagery, and other bitmap deliverables.

## Overlay Rules

- Read and follow the current system `$CODEX_HOME/skills/.system/imagegen/SKILL.md` for prompt guidance, taxonomy, model guidance, API parameters, transparent-image workflow, validation, and output handling.
- Override only the execution path: do not call the built-in `image_gen` tool directly from this skill.
- For actual generation/edit API calls, run this wrapper:

```bash
python "${CODEX_HOME:-$HOME/.codex}/skills/imagegen-configured/scripts/image_gen_configured.py" <system-imagegen-cli-args>
```

- The wrapper injects the current Codex provider credentials, then delegates to the latest system script at `$CODEX_HOME/skills/.system/imagegen/scripts/image_gen.py`.
- This keeps model/API behavior synced with future Codex updates while preserving configured `base_url` and API-key routing.

## Credential Routing

The wrapper resolves:

- `base_url` from the current provider in `$CODEX_HOME/config.toml`, falling back to `OPENAI_BASE_URL`.
- API key from provider `api_key`, provider env key, `$CODEX_HOME/auth.json`, or `OPENAI_API_KEY`.

It passes those values to the system imagegen CLI through `OPENAI_BASE_URL` and `OPENAI_API_KEY`. Never paste or print the full API key.

## Waiting

Image generation and editing commonly take 3 minutes or more.

After a real API request starts, keep waiting while the process is still running and there is no explicit error, disconnect, or timeout. Do not cancel or retry just because the terminal is quiet for several minutes; poll with longer waits until the process completes or fails.

## Usage Notes

- Use the current system imagegen docs to choose `generate`, `edit`, or `generate-batch` arguments.
- Use `--dry-run` first when checking payloads, output paths, or credential resolution.
- Use explicit `--out` or `--out-dir` paths so outputs are easy to find.
- For transparent chroma-key removal, use the helper from the system skill: `$CODEX_HOME/skills/.system/imagegen/scripts/remove_chroma_key.py`.
- If the system imagegen skill changes in a future Codex update, this wrapper should automatically use the updated system CLI behavior.

## Report Back

When finished, report:

- Final saved path(s).
- Whether the wrapper resolved a configured `base_url`.
- Any explicit error, disconnect, timeout, or validation issue encountered.
