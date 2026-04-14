from src.db.database import Database


class CompatibilityResolver:
    """Look up parts in the PartsCatalog table by OEM number or name query."""

    def __init__(self, db: Database):
        self.db = db

    def resolve_by_oem(self, oem_number: str) -> dict | None:
        """Return the catalog row for the given OEM number, or None."""
        conn = self.db._connect()
        cursor = conn.execute(
            "SELECT oem_number, part_name, category, compatible_models, "
            "enduro_specific, search_aliases "
            "FROM PartsCatalog WHERE oem_number = ?",
            (oem_number,),
        )
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return dict(row)

    def resolve_by_name(self, query: str) -> list[dict]:
        """Return all catalog rows where part_name, search_aliases, or category
        match the query (case-insensitive LIKE search)."""
        conn = self.db._connect()
        like_pattern = f"%{query}%"
        cursor = conn.execute(
            "SELECT oem_number, part_name, category, compatible_models, "
            "enduro_specific, search_aliases "
            "FROM PartsCatalog "
            "WHERE part_name LIKE ? OR search_aliases LIKE ? OR category LIKE ?",
            (like_pattern, like_pattern, like_pattern),
        )
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def is_enduro_specific(self, oem_number: str) -> bool | None:
        """Return True/False for the enduro_specific flag, or None if the part
        is not found."""
        row = self.resolve_by_oem(oem_number)
        if row is None:
            return None
        return bool(row["enduro_specific"])
