from fvn_translator.config import (
    ProjectConfig,
    load_project_config,
    load_providers,
    write_project_config,
    write_providers,
)
from fvn_translator.config.models import ProvidersConfig
from fvn_translator.models import ProviderConfig


def test_provider_config_round_trip_has_no_secret(tmp_path) -> None:
    path = tmp_path / "providers.toml"
    config = ProvidersConfig(
        active_provider="primary",
        providers={
            "primary": ProviderConfig(
                name="primary",
                type="openai-compatible",
                base_url="https://example.test/v1",
                model="model",
                secret_ref="fvn/primary",
            )
        },
    )
    write_providers(path, config)
    assert load_providers(path) == config
    assert "api_key" not in path.read_text(encoding="utf-8").lower()


def test_project_config_preserves_adapter_options(tmp_path) -> None:
    path = tmp_path / "project.toml"
    config = ProjectConfig(
        project_name="RenPy",
        source_root=tmp_path / "source",
        adapter_id="renpy",
        adapter_options={
            "profile_id": "remember-the-flowers-ii",
            "lint_enabled": True,
            "sdk_path": "D:/Tools/renpy-sdk",
        },
    )
    write_project_config(path, config)
    assert load_project_config(path) == config
