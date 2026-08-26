from __future__ import annotations

from pathlib import Path


def test_brick_reader_contract_is_declared_before_implementation() -> None:
    from vera_mmu.domain_packs.aret import AretBrickReadError, read_aret_v1_brick_page

    assert issubclass(AretBrickReadError, ValueError)
    assert callable(read_aret_v1_brick_page)


def test_brick_reader_module_has_no_write_or_network_capability() -> None:
    source = (Path(__file__).parents[1] / "src" / "vera_mmu" / "domain_packs" / "aret" / "brick_reader.py").read_text(encoding="utf-8")
    for required in ("FROM brick", "mode=ro&immutable=1", "SOURCE_ROWS_OBSERVED"):
        assert required in source
    for forbidden in ("INSERT", "UPDATE", "DELETE", "subprocess", "os.system", "requests", "urllib.", "socket"):
        assert forbidden not in source
