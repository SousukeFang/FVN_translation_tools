from pathlib import Path

from fvn_translator.adapters.contract_tests import run_adapter_contract_tests
from fvn_translator.adapters.renpy import RenPyAdapter


def test_renpy_adapter_contract(tmp_path: Path) -> None:
    fixture = Path("tests/fixtures/renpy_generic/source")
    run_adapter_contract_tests(RenPyAdapter(), fixture, tmp_path / "staging")
