from fvn_translator.adapters.contract_tests import run_adapter_contract_tests
from fvn_translator.adapters.demo import DemoAdapter


def test_demo_adapter_contract(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "chapter.demo").write_text(
        "[NARRATION] Quiet.\n[Fox] Hello {i}friend{/i}.\n", encoding="utf-8"
    )
    run_adapter_contract_tests(DemoAdapter(), source, tmp_path / "staging")
