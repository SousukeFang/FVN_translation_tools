from fvn_translator.profiles.base import FileDiscoveryRules, SceneRules

FILE_RULES = FileDiscoveryRules(
    exclude=(
        "game/tl/**",
        "game/renpy-ActionEditor3-master/**",
        "game/cache/**",
        "game/saves/**",
        "game/assetdefine.rpy",
        "game/characters/sprites*.rpy",
        "game/customeffects.rpy",
        "game/effects/**",
        "game/libs/**",
    ),
    categories={
        "story": ("game/story/**",),
        "ui": (
            "game/screens.rpy",
            "game/credits*.rpy",
            "game/extras.rpy",
            "game/extratext.rpy",
            "game/music_display.rpy",
            "game/music_room/**",
            "game/options.rpy",
        ),
        "characters": ("game/characters/names.rpy",),
    },
)

SCENE_RULES = SceneRules(
    boundaries=("label", "scene", "structured_comment"),
    structured_comments=(
        "scene",
        "location",
        "time",
        "chapter",
        "route",
        "translation note",
    ),
)
