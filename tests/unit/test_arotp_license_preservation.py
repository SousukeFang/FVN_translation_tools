from pathlib import Path
from zipfile import ZipFile

import pytest

from fvn_translator.adapters.base import AdapterConfig
from fvn_translator.adapters.renpy import RenPyAdapter
from fvn_translator.config import ProjectConfig
from fvn_translator.models import TranslationStatus, TranslationUnit
from fvn_translator.profiles.echo_project import ARoleToPlayProfile
from fvn_translator.services import ExtractionService, PatchService, ProjectService
from fvn_translator.storage import UnitRepository, Workspace
from fvn_translator.validators import validate_unit

ATTRIBUTION = "Kinetic Text Tags Ren'Py Module\nMIT License\nCopyright Synthetic Contributor\n"
CONFIG = AdapterConfig(options={"profile_id": "a-role-to-play"})


def _project(tmp_path: Path) -> tuple[Path, Workspace, UnitRepository, TranslationUnit]:
    source = tmp_path / "source"
    (source / "game").mkdir(parents=True)
    files = {
        "options.rpy": 'define config.name = _("A Role to Play")\n',
        "Week1.rpy": 'label start:\n    "A 10% slope."\n',
        "Week2.rpy": 'label week2:\n    "Another line."\n',
        "gui.rpy": f'"""{ATTRIBUTION}"""\n\nscreen notice():\n    text "Ready"\n',
    }
    for name, text in files.items():
        (source / "game" / name).write_bytes(
            b"\xef\xbb\xbf" + text.replace("\n", "\r\n").encode("utf-8")
        )
    adapter = RenPyAdapter()
    workspace = ProjectService().create(
        tmp_path / "workspace",
        ProjectConfig(
            project_name="Synthetic license case",
            source_root=source,
            adapter_id="renpy",
            adapter_options=CONFIG.options,
        ),
        adapter_version=adapter.adapter_version,
    )
    repository = UnitRepository(workspace.intermediate / "units.jsonl")
    ExtractionService(adapter, repository).extract(source, CONFIG)
    units = repository.load()
    attribution = next(unit for unit in units if "Synthetic Contributor" in unit.source_text)
    targets = {"A 10% slope.": "坡度为10%。", "Another line.": "另一句话。", "Ready": "就绪"}
    for unit in units:
        unit.target_text = targets.get(unit.source_text, unit.source_text)
        unit.translation.status = TranslationStatus.TRANSLATED
    repository.save(units)
    return source, workspace, repository, attribution


def _legacy_units(repository: UnitRepository) -> list[TranslationUnit]:
    units = repository.load()
    attribution = next(unit for unit in units if "Synthetic Contributor" in unit.source_text)
    for key in ("text_class", "player_visible", "preserve_original"):
        attribution.context.pop(key, None)
    attribution.protected_tokens.remove(attribution.source_text)
    return units


def test_module_attribution_is_classified_and_protected_without_removing_its_unit(
    tmp_path: Path,
) -> None:
    source, _, repository, attribution = _project(tmp_path)
    assert attribution.context["text_class"] == "module_license"
    assert attribution.context["player_visible"] is False
    assert attribution.context["preserve_original"] == "Third-party module license and attribution"
    assert attribution.source_text in attribution.protected_tokens
    legacy = _legacy_units(repository)
    reextracted = (
        RenPyAdapter()
        .extract(
            source,
            RenPyAdapter().discover_files(source, CONFIG),
            CONFIG,
        )
        .units
    )
    assert {unit.unit_id: unit.source_fingerprint for unit in reextracted} == {
        unit.unit_id: unit.source_fingerprint for unit in legacy
    }
    attribution.target_text = "修改过的许可致谢。"
    assert {issue.code for issue in validate_unit(attribution)} == {"PROTECTED_TOKEN_CHANGED"}


def test_legacy_workspace_packages_original_attribution_with_translated_gui(tmp_path: Path) -> None:
    source, workspace, repository, _ = _project(tmp_path)
    original = (source / "game/gui.rpy").read_bytes()
    repository.save(_legacy_units(repository))
    archive = PatchService(workspace).build(
        RenPyAdapter(),
        source,
        output_root=tmp_path / "output",
        config=CONFIG,
    )
    with ZipFile(archive) as zipped:
        gui = zipped.read("game/gui.rpy")
    assert f'"""{ATTRIBUTION}"""'.replace("\n", "\r\n").encode() in gui
    assert "就绪".encode() in gui
    assert gui.startswith(b"\xef\xbb\xbf") and b"\r\n" in gui
    assert (source / "game/gui.rpy").read_bytes() == original


def test_legacy_workspace_cannot_package_translated_attribution(tmp_path: Path) -> None:
    source, workspace, repository, _ = _project(tmp_path)
    legacy = _legacy_units(repository)
    attribution = next(unit for unit in legacy if "Synthetic Contributor" in unit.source_text)
    attribution.target_text = "修改过的许可致谢。\r\n"
    # Legacy public validation has no full-text protection; the profile must still stop it.
    assert not validate_unit(attribution)
    assert {
        issue.code for issue in ARoleToPlayProfile().validate_project(source, legacy).issues
    } == {"AROTP_MODULE_LICENSE_CHANGED"}
    repository.save(legacy)
    with pytest.raises(ValueError, match="Adapter validation failed"):
        PatchService(workspace).build(
            RenPyAdapter(),
            source,
            output_root=tmp_path / "output",
            config=CONFIG,
        )
    assert not (tmp_path / "output").exists()


def test_in_story_triple_quoted_text_is_not_classified_as_module_attribution(
    tmp_path: Path,
) -> None:
    source, _, _, _ = _project(tmp_path)
    (source / "game/Week1.rpy").write_text(f'label start:\n    """{ATTRIBUTION}"""\n')
    adapter = RenPyAdapter()
    result = adapter.extract(source, adapter.discover_files(source, CONFIG), CONFIG)
    story = next(unit for unit in result.units if unit.origin["path"] == "game/Week1.rpy")
    assert "text_class" not in story.context
    assert story.source_text not in story.protected_tokens


def test_declared_printf_templates_keep_public_and_renpy_validation_in_agreement(
    tmp_path: Path,
) -> None:
    source, _, _, _ = _project(tmp_path)
    (source / "game/zmessenger.rpy").write_text(
        "screen status():\n"
        '    $ message = Text("Value: % s" % value)\n'
        '    $ number = Text("Value: % 8.2f" % value)\n'
    )
    adapter = RenPyAdapter()
    result = adapter.extract(source, adapter.discover_files(source, CONFIG), CONFIG)
    templates = [unit for unit in result.units if unit.origin["path"] == "game/zmessenger.rpy"]
    assert [unit.protected_tokens for unit in templates] == [["% s"], ["% 8.2f"]]
    for unit in templates:
        unit.target_text = unit.source_text.replace("Value:", "值：")
        assert not validate_unit(unit)
    staging = tmp_path / "staging"
    adapter.apply(source, staging, result.units, CONFIG)
    assert not adapter.validate(staging, result.units, CONFIG).has_errors
    templates[0].target_text = "值："
    assert {issue.code for issue in validate_unit(templates[0])} == {"PROTECTED_TOKEN_CHANGED"}
