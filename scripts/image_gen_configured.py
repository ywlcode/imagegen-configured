#!/usr/bin/env python3
"""Run the current system imagegen CLI with Codex provider credentials."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Tuple


def _die(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def _codex_home() -> Path:
    return Path(os.getenv("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def _strip_toml_comment(line: str) -> str:
    in_quote = False
    escaped = False
    for idx, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = in_quote
            continue
        if char == '"':
            in_quote = not in_quote
            continue
        if char == "#" and not in_quote:
            return line[:idx].strip()
    return line.strip()


def _parse_toml_string(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        try:
            decoded = json.loads(value)
            return str(decoded)
        except Exception:
            return value[1:-1]
    return value


def _parse_toml_value(value: str) -> Any:
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return _parse_toml_string(value)
    if value == "true":
        return True
    if value == "false":
        return False
    return value


def _split_toml_dotted_key(value: str) -> List[str]:
    parts: List[str] = []
    buf: List[str] = []
    in_quote = False
    escaped = False
    for char in value.strip():
        if escaped:
            buf.append(char)
            escaped = False
            continue
        if char == "\\" and in_quote:
            buf.append(char)
            escaped = True
            continue
        if char == '"':
            buf.append(char)
            in_quote = not in_quote
            continue
        if char == "." and not in_quote:
            parts.append(_parse_toml_string("".join(buf).strip()))
            buf = []
            continue
        buf.append(char)
    if buf:
        parts.append(_parse_toml_string("".join(buf).strip()))
    return parts


def _read_codex_config(codex_home: Path) -> Dict[str, Any]:
    path = codex_home / "config.toml"
    config: Dict[str, Any] = {"model_provider": None, "model_providers": {}}
    if not path.exists():
        return config

    current_provider: Optional[str] = None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return config

    for raw in lines:
        line = _strip_toml_comment(raw)
        if not line:
            continue

        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            parts = _split_toml_dotted_key(section)
            if len(parts) >= 2 and parts[0] == "model_providers":
                current_provider = parts[1]
                config["model_providers"].setdefault(current_provider, {})
            else:
                current_provider = None
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = _parse_toml_string(key.strip())
        parsed = _parse_toml_value(value)
        if current_provider:
            config["model_providers"].setdefault(current_provider, {})[key] = parsed
        elif key == "model_provider":
            config["model_provider"] = parsed

    return config


def _read_auth_key(codex_home: Path, provider_name: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    path = codex_home / "auth.json"
    if not path.exists():
        return None, None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None, None

    if not isinstance(data, dict):
        return None, None

    provider_auth = data.get("model_providers")
    if provider_name and isinstance(provider_auth, dict):
        provider_data = provider_auth.get(provider_name)
        if isinstance(provider_data, dict):
            for key in ("api_key", "OPENAI_API_KEY", "openai_api_key"):
                value = provider_data.get(key)
                if isinstance(value, str) and value:
                    return value, f"Codex auth provider '{provider_name}'"

    for key in ("OPENAI_API_KEY", "api_key", "openai_api_key"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value, "Codex auth file"

    return None, None


DEFAULT_OPENAI_USER_AGENT = "CodexImagegen/1.0"


def _ensure_openai_custom_headers(env: Dict[str, str]) -> bool:
    headers = env.get("OPENAI_CUSTOM_HEADERS", "")
    lines = [line for line in headers.splitlines() if line.strip()]
    for line in lines:
        name, sep, _value = line.partition(":")
        if sep and name.strip().lower() == "user-agent":
            return False

    lines.append(f"User-Agent: {DEFAULT_OPENAI_USER_AGENT}")
    env["OPENAI_CUSTOM_HEADERS"] = "\n".join(lines)
    return True


def _resolve_provider_env() -> Tuple[Dict[str, str], Optional[str], Optional[str]]:
    codex_home = _codex_home()
    config = _read_codex_config(codex_home)
    provider_name = config.get("model_provider")
    provider: Dict[str, Any] = {}
    providers = config.get("model_providers")
    if provider_name and isinstance(providers, dict):
        candidate = providers.get(provider_name)
        if isinstance(candidate, dict):
            provider = candidate

    env = dict(os.environ)
    base_url_source: Optional[str] = None
    api_key_source: Optional[str] = None

    base_url = provider.get("base_url")
    if isinstance(base_url, str) and base_url:
        env["OPENAI_BASE_URL"] = base_url
        base_url_source = f"Codex config provider '{provider_name}'"
    elif env.get("OPENAI_BASE_URL"):
        base_url_source = "OPENAI_BASE_URL"

    api_key = provider.get("api_key")
    if isinstance(api_key, str) and api_key:
        env["OPENAI_API_KEY"] = api_key
        api_key_source = f"Codex config provider '{provider_name}'"

    provider_env_key = provider.get("env_key") or provider.get("api_key_env_var")
    if not api_key_source and isinstance(provider_env_key, str) and provider_env_key:
        env_value = env.get(provider_env_key)
        if env_value:
            env["OPENAI_API_KEY"] = env_value
            api_key_source = provider_env_key

    if not api_key_source:
        auth_key, source = _read_auth_key(codex_home, str(provider_name) if provider_name else None)
        if auth_key:
            env["OPENAI_API_KEY"] = auth_key
            api_key_source = source

    if not api_key_source and env.get("OPENAI_API_KEY"):
        api_key_source = "OPENAI_API_KEY"

    _ensure_openai_custom_headers(env)

    return env, base_url_source, api_key_source


def main() -> int:
    codex_home = _codex_home()
    system_script = codex_home / "skills" / ".system" / "imagegen" / "scripts" / "image_gen.py"
    if not system_script.exists():
        _die(f"System imagegen CLI not found: {system_script}")

    env, base_url_source, api_key_source = _resolve_provider_env()
    if api_key_source:
        print(f"API key resolved from {api_key_source}.", file=sys.stderr)
    else:
        print(
            "Warning: no API key resolved from Codex config/auth or OPENAI_API_KEY.",
            file=sys.stderr,
        )

    if base_url_source:
        print(f"Base URL resolved from {base_url_source}.", file=sys.stderr)
    else:
        print("Warning: no configured base_url resolved; using SDK default.", file=sys.stderr)

    argv = [sys.executable, str(system_script), *sys.argv[1:]]
    os.execvpe(sys.executable, argv, env)
    return 127


if __name__ == "__main__":
    raise SystemExit(main())
