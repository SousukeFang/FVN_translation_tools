import pytest

from fvn_translator.core.errors import ResponseFormatError
from fvn_translator.llm.response_parser import parse_translations


def test_strict_response_parser() -> None:
    assert parse_translations({"translations": [{"unit_id": "u", "target_text": "译"}]}, ["u"]) == {
        "u": "译"
    }
    with pytest.raises(ResponseFormatError):
        parse_translations({"translations": []}, ["u"])
    with pytest.raises(ResponseFormatError):
        parse_translations({"translations": [{"unit_id": "x", "target_text": "译"}]}, ["u"])
