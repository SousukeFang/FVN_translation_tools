import argparse
import json
from collections import Counter
from pathlib import Path
from uuid import uuid4

from . import __version__
from .core.errors import FVNError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fvn-translator")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command")
    agent = commands.add_parser(
        "agent", help="Translate through Agent file exchange, without an API"
    )
    actions = agent.add_subparsers(dest="action", required=True)
    prepare = actions.add_parser("prepare", help="Create a workspace and extract visible text")
    prepare.add_argument("--source", type=Path, required=True)
    prepare.add_argument("--workspace", type=Path, required=True)
    prepare.add_argument("--name")
    prepare.add_argument("--source-language", required=True)
    prepare.add_argument("--target-language", required=True)
    prepare.add_argument("--adapter", default="auto")
    prepare.add_argument("--profile")
    prepare.add_argument("--span-map", type=Path)
    prepare.add_argument("--source-version")
    export = actions.add_parser("export", help="Export pending translation tasks")
    export.add_argument("--workspace", type=Path, required=True)
    export.add_argument("--output", type=Path)
    export.add_argument("--max-chars", type=int, default=12000)
    export.add_argument("--context-units", type=int, default=3)
    importing = actions.add_parser("import", help="Validate and import one Agent response")
    importing.add_argument("--workspace", type=Path, required=True)
    importing.add_argument("--task", type=Path, required=True)
    importing.add_argument("--response", type=Path, required=True)
    importing.add_argument("--model")
    for name in ("status", "validate"):
        action = actions.add_parser(name)
        action.add_argument("--workspace", type=Path, required=True)
    package = actions.add_parser("package", help="Build a patch ZIP and installation instructions")
    package.add_argument("--workspace", type=Path, required=True)
    package.add_argument("--output", type=Path, required=True)
    package.add_argument("--extra", action="append", default=[], metavar="TARGET=SOURCE")
    package.add_argument("--extra-files", type=Path, help="JSON mapping patch paths to local files")
    package.add_argument("--install-notes", type=Path)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "agent":
        try:
            result = run_agent(args)
        except (FVNError, ValueError, KeyError, OSError) as error:
            parser.exit(2, f"{error}\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    from fvn_translator.tui import TranslatorApp

    TranslatorApp().run()


def run_agent(args: argparse.Namespace) -> dict[str, object]:
    from fvn_translator.adapters.base import AdapterConfig
    from fvn_translator.adapters.registry import default_registry
    from fvn_translator.config import ProjectConfig, load_project_config
    from fvn_translator.core.atomic_io import atomic_write_json
    from fvn_translator.services import ExtractionService, ProjectService, ValidationService
    from fvn_translator.services.agent_translation_service import AgentTranslationService
    from fvn_translator.services.patch_service import PatchService
    from fvn_translator.storage import UnitRepository, Workspace

    workspace = Workspace(args.workspace)
    registry = default_registry()
    if args.action == "prepare":
        source = args.source.expanduser().resolve()
        if not source.is_dir():
            raise ValueError(f"Source directory does not exist: {source}")
        if source == workspace.root or source.is_relative_to(workspace.root):
            raise ValueError("Keep source and workspace in separate, non-nested directories")
        if workspace.root.is_relative_to(source):
            raise ValueError("Keep source and workspace in separate, non-nested directories")
        if (workspace.intermediate / "manifest.json").exists():
            raise ValueError("Workspace already exists; export pending tasks to resume")
        adapter_id = args.adapter
        if args.span_map and adapter_id == "auto":
            adapter_id = "text-spans"
        if adapter_id == "auto":
            matches = []
            for candidate_id in registry.ids():
                candidate = registry.create(candidate_id)
                detection = candidate.detect(source)
                if detection.supported:
                    matches.append((detection.confidence, candidate_id))
            if not matches:
                raise ValueError("Identify the story text and provide --span-map; see generic.md")
            adapter_id = max(matches)[1]
        adapter = registry.create(adapter_id)
        options: dict[str, object] = {"target_language": args.target_language}
        if args.profile:
            options["profile_id"] = args.profile
        if args.span_map:
            options["map_path"] = str(args.span_map.expanduser().resolve())
        if args.source_version:
            options["source_version"] = args.source_version
        project = ProjectConfig(
            project_name=args.name or source.name,
            source_root=source,
            adapter_id=adapter_id,
            source_language=args.source_language,
            target_language=args.target_language,
            adapter_options=options,
        )
        workspace = ProjectService().create(
            workspace.root, project, adapter_version=adapter.adapter_version
        )
        with workspace:
            extraction = ExtractionService(
                adapter, UnitRepository(workspace.intermediate / "units.jsonl")
            )
            count = extraction.extract(source, AdapterConfig(options=options))
            report = extraction.last_result
            if report is None:
                raise RuntimeError("Extraction did not return a report")
            atomic_write_json(
                workspace.intermediate / "extraction_report.json", report.model_dump(mode="json")
            )
            if not count or any(issue.severity == "error" for issue in report.issues):
                raise ValueError("Extraction needs review; see intermediate/extraction_report.json")
        return {"workspace": str(workspace.root), "adapter": adapter_id, "units": count}

    project = load_project_config(workspace.root / "project.toml")
    repository = UnitRepository(workspace.intermediate / "units.jsonl")
    if args.action == "export":
        output = args.output or workspace.runs / "agent-tasks" / uuid4().hex[:12]
        tasks = AgentTranslationService(workspace).export_batches(
            output, max_chars=args.max_chars, context_units=args.context_units
        )
        return {"tasks": [str(path) for path in tasks], "batches": len(tasks)}
    if args.action == "import":
        count = AgentTranslationService(workspace).import_batch(
            args.task, args.response, model=args.model
        )
        return {"imported": count}
    if args.action == "status":
        units = repository.load()
        return {
            "project": project.project_name,
            "source_language": project.source_language,
            "target_language": project.target_language,
            "units": len(units),
            "statuses": dict(Counter(unit.translation.status.value for unit in units)),
        }
    adapter = registry.create(project.adapter_id)
    config = AdapterConfig(options=project.adapter_options)
    if args.action == "validate":
        with workspace:
            adapter.apply(project.source_root, workspace.staging, repository.load(), config)
            issues = ValidationService(
                repository, workspace.intermediate / "issues.jsonl"
            ).validate(adapter=adapter, staging_root=workspace.staging, config=config)
        if any(issue.severity == "error" for issue in issues):
            raise ValueError("Validation failed; see intermediate/issues.jsonl")
        return {"issues": [issue.model_dump(mode="json") for issue in issues]}
    extras: dict[str, Path] = {}
    if args.extra_files:
        extras.update(
            {
                key: Path(value)
                for key, value in json.loads(args.extra_files.read_text(encoding="utf-8")).items()
            }
        )
    for item in args.extra:
        if "=" not in item:
            raise ValueError("--extra expects TARGET=SOURCE")
        target, local = item.split("=", 1)
        extras[target] = Path(local)
    notes = args.install_notes.read_text(encoding="utf-8") if args.install_notes else ""
    patch = PatchService(workspace).build(
        adapter,
        project.source_root,
        output_root=args.output,
        config=config,
        extra_files=extras,
        install_notes=notes,
    )
    return {"patch": str(patch), "instructions": str(args.output / "README.md")}
