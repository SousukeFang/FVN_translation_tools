from fvn_translator.models import UnitType
from fvn_translator.profiles.base import CustomTextSink

CUSTOM_TEXT_SINKS = (
    CustomTextSink(function="Character", unit_type=UnitType.CHARACTER_NAME),
    CustomTextSink(function="Character", keyword="name", unit_type=UnitType.CHARACTER_NAME),
    CustomTextSink(function="renpy.notify", unit_type=UnitType.NOTIFICATION),
    CustomTextSink(function="renpy.input", unit_type=UnitType.INPUT_PROMPT),
)
