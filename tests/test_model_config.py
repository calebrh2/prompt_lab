from __future__ import annotations

from pathlib import Path

from promptlab.adapters.ollama import OllamaAdapter
from promptlab.config import PROJECT_ROOT, Settings

PACKAGE = PROJECT_ROOT / "src" / "promptlab"
MODEL_IDENTIFIERS = ("mistral:7b", "qwen3:8b")


def test_model_identifier_literals_live_only_in_configuration() -> None:
    leaked: list[str] = []
    for path in PACKAGE.rglob("*.py"):
        if path.name == "config.py":
            continue
        text = path.read_text(encoding="utf-8")
        for identifier in MODEL_IDENTIFIERS:
            if identifier in text:
                leaked.append(f"{path.relative_to(PROJECT_ROOT)}:{identifier}")
    assert leaked == []


def test_configured_models_use_ollama_and_distinct_model_ids() -> None:
    settings = Settings.from_env()
    assert set(settings.models) == {"mistral", "qwen"}
    adapters = {
        name: OllamaAdapter(model_id=config.model_id)
        for name, config in settings.models.items()
    }
    assert {adapter.provider for adapter in adapters.values()} == {"ollama"}
    model_ids = [adapter.model_id for adapter in adapters.values()]
    assert len(set(model_ids)) == 2
    for name, adapter in adapters.items():
        assert adapter.model_id == settings.models[name].model_id


def test_run_py_resolves_models_from_settings() -> None:
    source = Path("src/promptlab/run.py").read_text(encoding="utf-8")
    assert "settings.models[name].model_id" in source
    assert "OllamaAdapter" in source
    for identifier in MODEL_IDENTIFIERS:
        assert identifier not in source
