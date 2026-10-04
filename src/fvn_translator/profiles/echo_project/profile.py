import re
from pathlib import Path

from fvn_translator.adapters.base import ValidationReport
from fvn_translator.adapters.renpy.discovery import discover_renpy_files
from fvn_translator.adapters.renpy.lexer import RenPyLexer
from fvn_translator.adapters.renpy.statements.custom import literal_argument_index
from fvn_translator.models import Issue, Severity, TranslationUnit, UnitType
from fvn_translator.profiles.base import (
    CharacterDefinition,
    CustomTextSink,
    FileDiscoveryRules,
    ParseContext,
    ProfileDetectionResult,
    ProtectedTokenRules,
    SceneRules,
)

CHARACTER_ASSIGNMENT = re.compile(
    r"^[ \t]*(?:define[ \t]+|\$[ \t]+)?(?P<id>[A-Za-z_]\w*)"
    r"[ \t]*=[ \t]*Character[ \t]*\(",
    re.MULTILINE,
)
COMMON_EXCLUDES = ("game/tl/**", "game/cache/**", "game/saves/**")
ROUTE65_NAMES = {
    "l": "Leo",
    "t": "TJ",
    "c": "Carl",
    "f": "Flynn",
    "j": "Jasmynn",
    "m": "Chase",
    "ku": "Kudzu",
    "cl": "Clint",
    "jer": "Jeremy",
    "ra": "Raven",
    "du": "Duke",
    "br": "Brian",
    "ja": "Janice",
    "sy": "Sydney",
    "ch": "Charlie",
    "k": "Karen",
}


class EchoProjectProfile:
    """Shared Ren'Py text handling, with separate game identities and source rules."""

    profile_id = ""
    profile_version = "1.0.0"
    engine_adapter_id = "renpy"
    title = ""
    story_files: tuple[str, ...] = ()
    extra_excludes: tuple[str, ...] = ()

    def detect(self, source_root: Path) -> ProfileDetectionResult:
        options = source_root / "game/options.rpy"
        if not options.is_file():
            return ProfileDetectionResult(supported=False, confidence=0, reason="options missing")
        text = options.read_bytes().decode("utf-8-sig", errors="replace")
        named = bool(
            re.search(
                rf"\bconfig\.name\s*=\s*(?:_\(\s*)?['\"]{re.escape(self.title)}['\"]",
                text,
            )
        )
        supported = named and all(
            (source_root / "game" / filename).is_file() for filename in self.story_files
        )
        return ProfileDetectionResult(
            supported=supported,
            confidence=1.0 if supported else 0.4 if named else 0.0,
            reason="config.name and story files" if supported else "signature incomplete",
        )

    def get_file_rules(self) -> FileDiscoveryRules:
        return FileDiscoveryRules(
            exclude=(*COMMON_EXCLUDES, *self.extra_excludes),
            categories={
                "story": tuple(f"game/{name}" for name in self.story_files),
                "ui": ("game/screens.rpy", "game/gallery.rpy", "game/music_room/music_room.rpy"),
                "characters": ("game/script.rpy",),
                "configuration": ("game/options.rpy", "game/gui.rpy"),
            },
        )

    def get_character_map(self, source_root: Path) -> dict[str, CharacterDefinition]:
        characters = _load_character_map(source_root, self.get_file_rules())
        for speaker_id in ("narrator", "centered"):
            characters.setdefault(
                speaker_id,
                CharacterDefinition(speaker_id=speaker_id, status="builtin"),
            )
        if self.profile_id == "echo-route-65":
            # This release draws speaker names as UI images; its Character names are blank.
            for speaker_id, display_name in ROUTE65_NAMES.items():
                if speaker_id in characters and not characters[speaker_id].display_name:
                    characters[speaker_id] = characters[speaker_id].model_copy(
                        update={"display_name": display_name, "status": "context_only"}
                    )
        return characters

    def get_custom_text_sinks(self) -> list[CustomTextSink]:
        return [
            CustomTextSink(function="Character", unit_type=UnitType.CHARACTER_NAME),
            CustomTextSink(function="Character", keyword="name", unit_type=UnitType.CHARACTER_NAME),
            CustomTextSink(function="renpy.input", unit_type=UnitType.INPUT_PROMPT),
            CustomTextSink(function="renpy.notify", unit_type=UnitType.NOTIFICATION),
        ]

    def get_scene_rules(self) -> SceneRules:
        return SceneRules()

    def get_protected_token_rules(self) -> ProtectedTokenRules:
        return ProtectedTokenRules()

    def enrich_unit(self, unit: TranslationUnit, context: ParseContext) -> TranslationUnit:
        if unit.speaker == "narrator":
            unit.type = UnitType.NARRATION
        elif unit.speaker in {"centered", "centertext"}:
            unit.type = UnitType.SCREEN_TEXT
        prefix = str(unit.adapter_data.get("statement_prefix", ""))
        if context.relative_path == "game/options.rpy" and re.match(
            r"\s*(?:define\s+)?config\.name\s*=", prefix
        ):
            unit.protected_tokens = list(dict.fromkeys([*unit.protected_tokens, unit.source_text]))
            unit.context["preserve_original"] = "Game title"
        return unit

    def validate_project(
        self, staging_root: Path, units: list[TranslationUnit]
    ) -> ValidationReport:
        return ValidationReport(issues=[])


class EchoRoute65Profile(EchoProjectProfile):
    profile_id = "echo-route-65"
    title = "Echo"
    story_files = ("Saturday.rpy", "Carl.rpy", "Jas.rpy", "TJ.rpy")


class KhemiaProfile(EchoProjectProfile):
    profile_id = "khemia"
    title = "Khemia"
    story_files = ("a1s1.rpy", "a1s2.rpy", "a1s3.rpy", "a2s1.rpy", "a2s2.rpy")
    extra_excludes = (
        "game/music_room/01_music_room_backend.rpy",
        "game/textbox_transitions.rpy",
    )


class IntereaProfile(EchoProjectProfile):
    profile_id = "interea"
    title = "Interea"
    story_files = ("a1s1.rpy", "a1s2.rpy", "a1s3.rpy", "a1s4.rpy")


class ARoleToPlayProfile(EchoProjectProfile):
    profile_id = "a-role-to-play"
    title = "A Role to Play"
    story_files = ("Week1.rpy", "Week2.rpy")
    extra_excludes = (
        "game/ActionEditor.rpy",
        "game/00camera_statements.rpy",
        "game/camera.rpy",
        "game/camera_config.rpy",
        "game/image_viewer.rpy",
        "game/keymap.rpy",
        "game/spline.rpy",
        "game/000warpers.rpy",
        "game/00warper.rpy",
        "game/testing_room.rpy",
        "game/zTesting_ground.rpy",
    )

    def get_character_map(self, source_root: Path) -> dict[str, CharacterDefinition]:
        characters = super().get_character_map(source_root)
        # DynamicCharacter's first argument is Python code, not a visible name.
        characters.setdefault("nm", CharacterDefinition(speaker_id="nm", status="dynamic"))
        return characters

    def get_custom_text_sinks(self) -> list[CustomTextSink]:
        return [
            *super().get_custom_text_sinks(),
            CustomTextSink(function="msg", unit_type=UnitType.DIALOGUE),
            CustomTextSink(function="msg", keyword="what", unit_type=UnitType.DIALOGUE),
            CustomTextSink(
                function="msg",
                keyword="choices",
                dictionary_value_key="name",
                unit_type=UnitType.MENU_CHOICE,
            ),
            CustomTextSink(function="chat.addmessage_pc", argument=2, unit_type=UnitType.DIALOGUE),
            CustomTextSink(function="GalleryItem", unit_type=UnitType.UI_TEXT),
            CustomTextSink(function="GalleryItem", keyword="name", unit_type=UnitType.UI_TEXT),
            CustomTextSink(function="Text", literal_fragments=True, unit_type=UnitType.UI_TEXT),
            CustomTextSink(
                function="switch_dialogue", keyword="name", unit_type=UnitType.CHARACTER_NAME
            ),
            CustomTextSink(function="Interlocutor", argument=1, unit_type=UnitType.CHARACTER_NAME),
            CustomTextSink(
                function="Interlocutor", keyword="name", unit_type=UnitType.CHARACTER_NAME
            ),
        ]

    def enrich_unit(self, unit: TranslationUnit, context: ParseContext) -> TranslationUnit:
        unit = super().enrich_unit(unit, context)
        if _is_arotp_module_license(unit):
            # Keep the registered unit and fingerprint stable for existing workspaces.
            # This top-level attribution is implementation documentation, not dialogue.
            unit.context.update(
                text_class="module_license",
                player_visible=False,
                preserve_original="Third-party module license and attribution",
            )
            unit.protected_tokens = list(dict.fromkeys([*unit.protected_tokens, unit.source_text]))
        if context.relative_path == "game/zmessenger.rpy":
            # Preserve old %-format interpolation in phone display templates.
            formats = re.findall(
                r"%(?:\([^)]+\))?[#0 +\-]*\d*(?:\.\d+)?[diouxXeEfFgGcrs%]", unit.source_text
            )
            unit.protected_tokens = list(dict.fromkeys([*unit.protected_tokens, *formats]))
        if unit.context.get("semantic_role") == "function" and unit.adapter_data.get(
            "function"
        ) in {"switch_dialogue", "Interlocutor"}:
            # These names also construct avatar resource paths in this game.
            unit.protected_tokens = list(dict.fromkeys([*unit.protected_tokens, unit.source_text]))
            unit.context["preserve_original"] = "Phone avatar lookup name"
        return unit

    def validate_project(
        self, staging_root: Path, units: list[TranslationUnit]
    ) -> ValidationReport:
        issues = []
        for unit in units:
            if not unit.target_text or unit.target_text == unit.source_text:
                continue
            if unit.context.get("preserve_original") == "Phone avatar lookup name":
                issues.append(
                    Issue(
                        issue_id=f"arotp-resource-name:{unit.unit_id}",
                        code="AROTP_RESOURCE_NAME_CHANGED",
                        severity=Severity.ERROR,
                        message=(
                            "Phone name also selects an avatar resource "
                            "and must retain its source value"
                        ),
                        unit_id=unit.unit_id,
                        path=str(unit.origin["path"]),
                        line=int(unit.origin["line"]),
                    )
                )
            if _is_arotp_module_license(unit):
                issues.append(
                    Issue(
                        issue_id=f"arotp-module-license:{unit.unit_id}",
                        code="AROTP_MODULE_LICENSE_CHANGED",
                        severity=Severity.ERROR,
                        message=(
                            "Third-party module license and attribution must retain the source text"
                        ),
                        unit_id=unit.unit_id,
                        path=str(unit.origin["path"]),
                        line=int(unit.origin["line"]),
                    )
                )
        return ValidationReport(issues=issues)


def _is_arotp_module_license(unit: TranslationUnit) -> bool:
    """Recognize original metadata too, without relying on a release's line or ID."""
    return (
        unit.origin.get("path") == "game/gui.rpy"
        and unit.adapter_data.get("label") == "<file>"
        and unit.adapter_data.get("node_kind") == "say"
        and unit.adapter_data.get("quote") in {'"""', "'''"}
        and unit.source_text.lstrip().startswith("Kinetic Text Tags Ren'Py Module")
    )


def _load_character_map(
    source_root: Path, file_rules: FileDiscoveryRules
) -> dict[str, CharacterDefinition]:
    result: dict[str, CharacterDefinition] = {}
    for source_file in discover_renpy_files(source_root, file_rules):
        text = (source_root / source_file.relative_path).read_bytes().decode("utf-8-sig")
        lexed = RenPyLexer().scan(text, source_file.relative_path)
        code = list(text)
        for token in lexed.strings:
            for index in range(token.start, token.end):
                if code[index] not in "\r\n":
                    code[index] = " "
        # Assignment matching runs against source code, never strings or comments.
        masked = re.sub(r"#[^\r\n]*", lambda match: " " * len(match.group()), "".join(code))
        for match in CHARACTER_ASSIGNMENT.finditer(masked):
            end = _call_end(masked, match.end())
            strings = [token for token in lexed.strings if match.end() <= token.start < end]
            display = None
            for token in strings:
                arguments = {
                    literal_argument_index(
                        text,
                        function="Character",
                        token=token,
                        statement_start=match.start(),
                        statement_end=end,
                        strings=strings,
                        keyword=keyword,
                    )
                    for keyword in (None, "name")
                }
                if 0 in arguments:
                    display = token.value if token.value.strip() else None
                    break
            speaker_id = match.group("id")
            result[speaker_id] = CharacterDefinition(
                speaker_id=speaker_id,
                display_name=display,
                status="resolved" if display else "unresolved",
                source_path=source_file.relative_path,
                source_line=text.count("\n", 0, match.start()) + 1,
            )
    return result


def _call_end(masked: str, start: int) -> int:
    depth = 1
    for index in range(start, len(masked)):
        if masked[index] == "(":
            depth += 1
        elif masked[index] == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    return len(masked)
