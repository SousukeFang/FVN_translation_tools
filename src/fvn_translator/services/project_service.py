from pathlib import Path
from uuid import uuid4

from fvn_translator.config import ProjectConfig, write_project_config
from fvn_translator.models import Manifest
from fvn_translator.storage import Workspace


class ProjectService:
    def create(
        self, workspace_root: Path, config: ProjectConfig, *, adapter_version: str
    ) -> Workspace:
        workspace = Workspace.create(workspace_root)
        write_project_config(workspace.root / "project.toml", config)
        manifest = Manifest(
            project_id=uuid4().hex,
            project_name=config.project_name,
            source_language=config.source_language,
            target_language=config.target_language,
            source_format=config.adapter_id,
            adapter_id=config.adapter_id,
            adapter_version=adapter_version,
            source_root=str(config.source_root.resolve()),
            prompt_versions={
                "translation": "translation-v1",
                "metadata": "metadata-v1",
                "summary": "summary-v1",
            },
        )
        workspace.write_manifest(manifest.model_dump(mode="json", by_alias=True))
        return workspace
