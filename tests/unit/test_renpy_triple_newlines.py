"""Synthetic mixed-spelling triples preserve semantic and raw newline guards."""

import ast
import base64
import importlib.util
import json
from pathlib import Path

import pytest

from fvn_translator.adapters.base import AdapterConfig
from fvn_translator.adapters.renpy import RenPyAdapter
from fvn_translator.adapters.renpy.lexer import decode_string_content
from fvn_translator.adapters.renpy.protected_tokens import compare_signatures, protection_signature
from fvn_translator.adapters.renpy.writer import encode_string_content
from fvn_translator.config import ProjectConfig
from fvn_translator.core.atomic_io import atomic_write_json
from fvn_translator.services import ExtractionService, ProjectService
from fvn_translator.services.agent_translation_service import AgentTranslationService
from fvn_translator.storage import UnitRepository


@pytest.mark.parametrize("physical", ["\n", "\r\n"])
def test_mixed_triple_keeps_ordered_physical_and_escaped_newlines(physical):
    raw = (
        physical
        + r"One\nTwo\n"
        + physical
        + r"Three\nFour\n"
        + physical
        + r"Five\nSix\n"
        + physical
    )
    source = decode_string_content(raw)
    target = source.replace("One", "甲").replace("Two", "乙")
    rendered = encode_string_content(target, quote='"""', source_raw_content=raw)
    assert rendered.count("\n") == 4
    assert rendered.count(r"\n") == 6
    assert decode_string_content(rendered) == target
    assert ast.literal_eval('"""' + rendered + '"""') == target.replace("\r\n", "\n")
    assert not compare_signatures(
        protection_signature(source, raw), protection_signature(target, rendered)
    )
    for changed in (target + "\n", target.replace("\n", "", 1)):
        with pytest.raises(ValueError, match="semantic newline sequence"):
            encode_string_content(changed, quote='"""', source_raw_content=raw)


def test_literal_backslash_n_is_not_a_semantic_triple_newline():
    raw = r"Literal \\n then\nnewline" + "\n"
    source = decode_string_content(raw)
    rendered = encode_string_content(
        source.replace("Literal", "字面量"), quote='"""', source_raw_content=raw
    )
    assert rendered.startswith(r"字面量 \\n")
    assert decode_string_content(rendered) == source.replace("Literal", "字面量")


def test_writer_and_reextraction_accept_synthetic_mixed_triple(tmp_path):
    source = tmp_path / "source"
    (source / "game").mkdir(parents=True)
    raw = "\r\n" + r"One\nTwo\n" + "\r\n" + r"Three\nFour\n" + "\r\n" + r"Five\nSix\n" + "\r\n"
    data = ('define config.about = _("""' + raw + '""")\r\n').encode()
    (source / "game/options.rpy").write_bytes(data)
    adapter, config = RenPyAdapter(), AdapterConfig()
    units = adapter.extract(source, adapter.discover_files(source, config), config).units
    assert len(units) == 1
    units[0].target_text = units[0].source_text.replace("One", "第一").replace("Two", "第二")
    staging = tmp_path / "staging"
    adapter.apply(source, staging, units, config)
    assert not adapter.validate(staging, units, config).has_errors
    assert (source / "game/options.rpy").read_bytes() == data


def test_formal_delta_uses_the_same_mixed_triple_spelling_as_staging(tmp_path):
    helper = (
        Path(__file__).resolve().parents[2] / "skills/fvn-translate/scripts/build_renpy_delta.py"
    )
    spec = importlib.util.spec_from_file_location("triple_delta_test", helper)
    assert spec and spec.loader
    delta = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(delta)
    source = tmp_path / "source"
    (source / "game").mkdir(parents=True)
    raw = "\r\n" + r"One\nTwo\n" + "\r\n" + r"Three\nFour\n" + "\r\n" + r"Five\nSix\n" + "\r\n"
    original = ('define config.about = _("""' + raw + '""")\r\n').encode()
    (source / "game/options.rpy").write_bytes(original)
    workspace = ProjectService().create(
        tmp_path / "workspace",
        ProjectConfig(
            project_name="Synthetic mixed triple",
            source_root=source,
            adapter_id="renpy",
            target_language="zh-CN",
        ),
        adapter_version=RenPyAdapter.adapter_version,
    )
    repository = UnitRepository(workspace.intermediate / "units.jsonl")
    ExtractionService(RenPyAdapter(), repository).extract(source)
    unit = repository.load()[0]
    target = unit.source_text.replace("One", "第一").replace("Two", "第二")
    service = AgentTranslationService(workspace)
    task = service.export_batches(tmp_path / "tasks", unit_ids={unit.unit_id})[0]
    response = tmp_path / "response.json"
    atomic_write_json(
        response, {"translations": [{"unit_id": unit.unit_id, "target_text": target}]}
    )
    service.import_batch(task, response, model="offline-synthetic-triple-test")
    manifest_path = delta.build_delta(
        workspace,
        source_root=source,
        unit_ids=[unit.unit_id],
        output_root=tmp_path / "patch",
        patch_id="mixed-triple",
    )
    manifest = json.loads(manifest_path.read_text())
    replacement = manifest["files"][0]["replacements"][0]
    rendered = base64.b64decode(replacement["replacement_base64"]).decode()
    assert rendered.count("\n") == 4 and rendered.count(r"\n") == 6
    assert decode_string_content(rendered) == target
    assert (source / "game/options.rpy").read_bytes() == original
