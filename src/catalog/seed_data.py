import json
from pathlib import Path

from src.db.database import Database


def load_seed_data(seed_path: str) -> list[dict]:
    """Read a seed JSON file and return a flat list of part dicts.

    Each dict contains: oem_number, part_name, category,
    compatible_models (JSON string), enduro_specific (bool),
    search_aliases (JSON string).
    """
    path = Path(seed_path)
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    model_name = raw["model"]
    parts_section = raw["parts"]
    result: list[dict] = []

    for part in parts_section.get("enduro_specific", []):
        result.append({
            "oem_number": part["oem_number"],
            "part_name": part["part_name"],
            "category": part["category"],
            "compatible_models": json.dumps([model_name]),
            "enduro_specific": True,
            "search_aliases": json.dumps(part.get("search_aliases", [])),
        })

    for part in parts_section.get("shared", []):
        compatible = [model_name] + part.get("compatible_with", [])
        result.append({
            "oem_number": part["oem_number"],
            "part_name": part["part_name"],
            "category": part["category"],
            "compatible_models": json.dumps(compatible),
            "enduro_specific": False,
            "search_aliases": json.dumps(part.get("search_aliases", [])),
        })

    return result


def seed_database(db: Database, seed_path: str) -> None:
    """Insert seed data into the PartsCatalog table."""
    parts = load_seed_data(seed_path)
    conn = db._connect()
    for part in parts:
        conn.execute(
            "INSERT OR REPLACE INTO PartsCatalog "
            "(oem_number, part_name, category, compatible_models, enduro_specific, search_aliases) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                part["oem_number"],
                part["part_name"],
                part["category"],
                part["compatible_models"],
                int(part["enduro_specific"]),
                part["search_aliases"],
            ),
        )
    conn.commit()
    conn.close()
