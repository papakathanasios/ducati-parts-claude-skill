from pathlib import Path
from src.catalog.seed_data import load_seed_data, seed_database
from src.catalog.compatibility import CompatibilityResolver
from src.db.database import Database

SEED_PATH = str(Path(__file__).parent.parent / "data" / "seed" / "multistrada_1260_enduro.json")


def test_load_seed_data():
    parts = load_seed_data(SEED_PATH)
    assert len(parts) > 0
    enduro_parts = [p for p in parts if p["enduro_specific"]]
    shared_parts = [p for p in parts if not p["enduro_specific"]]
    assert len(enduro_parts) >= 8
    assert len(shared_parts) >= 8


def test_compatibility_resolver_oem_lookup(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    seed_database(db, SEED_PATH)
    resolver = CompatibilityResolver(db)
    result = resolver.resolve_by_oem("63040601A")
    assert result is not None
    assert result["enduro_specific"] == 0
    assert "Multistrada 1260" in result["compatible_models"]
    result = resolver.resolve_by_oem("96481712A")
    assert result is not None
    assert result["enduro_specific"] == 1


def test_compatibility_resolver_by_query(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    seed_database(db, SEED_PATH)
    resolver = CompatibilityResolver(db)
    matches = resolver.resolve_by_name("clutch lever")
    assert len(matches) >= 1
    assert any("Clutch" in m["part_name"] for m in matches)


def test_compatibility_resolver_unknown_part(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    seed_database(db, SEED_PATH)
    resolver = CompatibilityResolver(db)
    result = resolver.resolve_by_oem("UNKNOWN123")
    assert result is None
