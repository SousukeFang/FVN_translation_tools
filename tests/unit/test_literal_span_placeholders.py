from pathlib import Path

from fvn_translator.adapters.base import AdapterConfig
from fvn_translator.adapters.text_spans import TextSpanAdapter
from fvn_translator.models import TranslationStatus
from fvn_translator.validators import validate_unit


def test_literal_bracket_caption_and_declared_variable_have_distinct_protection(tmp_path: Path):
    import json

    source = tmp_path / "source"
    source.mkdir()
    text = "[Click thumbnail to enlarge] by [username]"
    (source / "caption.txt").write_text(text)
    mapping = tmp_path / "map.json"
    mapping.write_text(
        json.dumps(
            {
                "files": [
                    {
                        "path": "caption.txt",
                        "spans": [
                            {
                                "start": 0,
                                "end": len(text),
                                "source_text": text,
                                "placeholder_mode": "explicit",
                                "protected_tokens": ["[username]"],
                            }
                        ],
                    }
                ]
            }
        )
    )
    adapter = TextSpanAdapter()
    config = AdapterConfig(options={"map_path": str(mapping)})
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    unit = result.units[0]
    assert unit.protected_tokens == ["[username]"]
    unit.target_text = "【点击缩略图放大】作者 [username]"
    unit.translation.status = TranslationStatus.TRANSLATED
    assert not validate_unit(unit)
    staging = tmp_path / "staging"
    adapter.apply(source, staging, [unit], config)
    assert not adapter.validate(staging, [unit], config).has_errors
    assert (staging / "caption.txt").read_text() == unit.target_text
    unit.target_text = "【点击缩略图放大】作者"
    assert any(issue.code == "PROTECTED_TOKEN_CHANGED" for issue in validate_unit(unit))


def test_span_placeholder_inference_remains_default(tmp_path: Path):
    import json

    source = tmp_path / "source"
    source.mkdir()
    text = "[name] {i}Ready{/i}"
    (source / "caption.txt").write_text(text)
    mapping = tmp_path / "map.json"
    mapping.write_text(
        json.dumps(
            {
                "files": [
                    {
                        "path": "caption.txt",
                        "spans": [
                            {
                                "start": 0,
                                "end": len(text),
                                "source_text": text,
                            }
                        ],
                    }
                ]
            }
        )
    )
    adapter = TextSpanAdapter()
    config = AdapterConfig(options={"map_path": str(mapping)})
    unit = adapter.extract(source, adapter.discover_files(source, config), config).units[0]
    assert unit.protected_tokens == ["[name]", "{i}", "{/i}"]
    unit.target_text = "准备好了"
    assert any(issue.code == "PROTECTED_TOKEN_CHANGED" for issue in validate_unit(unit))
