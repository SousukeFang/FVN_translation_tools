import json
import tomllib
from pathlib import Path

from fvn_translator.core.atomic_io import atomic_write_text
from fvn_translator.models import ProviderConfig

from .models import ProjectConfig, ProvidersConfig


def load_project_config(path: Path) -> ProjectConfig:
    with path.open("rb") as stream:
        return ProjectConfig.model_validate(tomllib.load(stream))


def write_project_config(path: Path, config: ProjectConfig) -> None:
    rows = [
        f"project_name = {json.dumps(config.project_name, ensure_ascii=False)}",
        f"source_root = {json.dumps(str(config.source_root), ensure_ascii=False)}",
        f"adapter_id = {json.dumps(config.adapter_id)}",
        f"source_language = {json.dumps(config.source_language)}",
        f"target_language = {json.dumps(config.target_language)}",
    ]
    if config.adapter_options:
        rows.extend(("", "[adapter_options]"))
        for key, value in sorted(config.adapter_options.items()):
            if value is not None:
                rows.append(f"{key} = {_toml_value(value)}")
    atomic_write_text(path, "\n".join(rows) + "\n")


def _toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, Path):
        return json.dumps(str(value), ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        pairs = [f"{key} = {_toml_value(item)}" for key, item in sorted(value.items())]
        return "{ " + ", ".join(pairs) + " }"
    raise TypeError(f"Unsupported project TOML value: {type(value).__name__}")


def load_providers(path: Path) -> ProvidersConfig:
    if not path.exists():
        return ProvidersConfig()
    with path.open("rb") as stream:
        raw = tomllib.load(stream)
    providers = {
        str(name): ProviderConfig.model_validate({"name": name, **value})
        for name, value in raw.get("providers", {}).items()
    }
    return ProvidersConfig(active_provider=raw.get("active_provider", "mock"), providers=providers)


def write_providers(path: Path, config: ProvidersConfig) -> None:
    rows = [f"active_provider = {json.dumps(config.active_provider)}"]
    for name, provider in sorted(config.providers.items()):
        rows.extend(("", f"[providers.{name}]", f"type = {json.dumps(provider.type)}"))
        for key in (
            "base_url",
            "model",
            "secret_ref",
            "timeout_seconds",
            "max_retries",
            "temperature",
            "max_concurrency",
        ):
            value = getattr(provider, key)
            if value is None:
                continue
            if key == "base_url":
                value = str(value)
            encoded = json.dumps(value, ensure_ascii=False) if isinstance(value, str) else value
            rows.append(f"{key} = {encoded}")
    atomic_write_text(path, "\n".join(rows) + "\n")
