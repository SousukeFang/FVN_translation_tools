from fvn_translator.models import UnitType
from fvn_translator.profiles.base import CustomTextSink, FileDiscoveryRules
from fvn_translator.profiles.echo_project.profile import EchoProjectProfile

JOURNAL_TEXT_VARIABLES = (
    "chnighttext",
    "stagnighttext",
    "cynthiatext",
    "jamestext",
    "portertext",
    "changtext",
    "huxley1",
    "huxley2",
    "huxley3",
    "etheltext",
    "harlantext",
    "huxley4",
    "gumtext",
    "kanetext",
    "filmtext",
    "jartext",
    "dolltext",
    "marcydolltext",
    "samtoddtext",
    "shroudtext",
    "murdochtext",
    "portraittext",
    "manortext",
    "hledgertext",
    "hlettertext",
    "ethelclifftext",
)


class TheSmokeRoomProfile(EchoProjectProfile):
    profile_id = "the-smoke-room"
    title = "The Smoke Room"
    story_files = (
        "commonroute.rpy",
        "nikroute.rpy",
        "nikroute2.rpy",
        "nikroute3.rpy",
        "nikroute4.rpy",
        "nikroute4b.rpy",
        "nikselect.rpy",
        "williamroute.rpy",
        "williamroute2.rpy",
        "williamroute3.rpy",
        "willselect.rpy",
        "Murdochroute.rpy",
        "murdochroute2.rpy",
        "murdochroute3.rpy",
        "murdochroute4.rpy",
        "murdochroute4b.rpy",
        "murdochselect.rpy",
        "cliffroute.rpy",
        "cliffroute2.rpy",
        "cliffroute3.rpy",
        "cliffselect.rpy",
    )

    def get_file_rules(self) -> FileDiscoveryRules:
        rules = super().get_file_rules()
        return rules.model_copy(
            update={
                "categories": {
                    **rules.categories,
                    "ui": ("game/screens.rpy", "game/credits.rpy"),
                    "characters": ("game/script.rpy", "game/recolorsbase.rpy"),
                }
            }
        )

    def get_custom_text_sinks(self) -> list[CustomTextSink]:
        return [
            *super().get_custom_text_sinks(),
            CustomTextSink(function="Text", literal_fragments=True, unit_type=UnitType.UI_TEXT),
            CustomTextSink(
                assignment_target="journal_entries",
                dictionary_value_key="text",
                unit_type=UnitType.UI_TEXT,
            ),
            CustomTextSink(assignment_target="spoiler_message", unit_type=UnitType.UI_TEXT),
            CustomTextSink(assignment_target="investigorder", unit_type=UnitType.UI_TEXT),
            CustomTextSink(
                assignment_target="murdochchoices",
                excluded_values=("ral", "jim", "mel", "bli"),
                unit_type=UnitType.UI_TEXT,
            ),
            *(
                CustomTextSink(assignment_target=target, unit_type=UnitType.UI_TEXT)
                for target in JOURNAL_TEXT_VARIABLES
            ),
        ]
