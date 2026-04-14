import sqlite3
from datetime import datetime
from pathlib import Path


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def initialize(self) -> None:
        conn = self._connect()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS Listing (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                part_price REAL NOT NULL,
                shipping_price REAL NOT NULL,
                total_price REAL NOT NULL,
                shipping_ratio_flag INTEGER NOT NULL,
                currency_original TEXT NOT NULL,
                seller_country TEXT NOT NULL,
                is_eu INTEGER NOT NULL,
                condition_raw TEXT NOT NULL,
                condition_score TEXT NOT NULL,
                condition_notes TEXT NOT NULL,
                photos TEXT NOT NULL,
                listing_url TEXT NOT NULL,
                compatible_models TEXT NOT NULL,
                compatibility_confidence TEXT NOT NULL,
                oem_part_number TEXT NOT NULL,
                date_listed TEXT NOT NULL,
                date_found TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS Watch (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                part_category TEXT NOT NULL DEFAULT '',
                oem_number TEXT NOT NULL DEFAULT '',
                max_total_price REAL NOT NULL,
                target_models TEXT NOT NULL DEFAULT '[]',
                sources TEXT NOT NULL DEFAULT '[]',
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                last_checked TEXT
            );

            CREATE TABLE IF NOT EXISTS SeenListing (
                listing_id TEXT NOT NULL,
                watch_id INTEGER NOT NULL,
                first_seen TEXT NOT NULL DEFAULT (datetime('now')),
                notified INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (listing_id, watch_id),
                FOREIGN KEY (watch_id) REFERENCES Watch(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS PartsCatalog (
                oem_number TEXT PRIMARY KEY,
                part_name TEXT NOT NULL,
                category TEXT NOT NULL,
                compatible_models TEXT NOT NULL DEFAULT '[]',
                enduro_specific INTEGER NOT NULL DEFAULT 0,
                search_aliases TEXT NOT NULL DEFAULT '[]'
            );
        """)
        conn.commit()
        conn.close()

    def upsert_listing(self, data: dict) -> None:
        conn = self._connect()
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        updates = ", ".join(f"{k}=excluded.{k}" for k in data if k != "id")
        conn.execute(
            f"INSERT INTO Listing ({columns}) VALUES ({placeholders}) "
            f"ON CONFLICT(id) DO UPDATE SET {updates}",
            list(data.values()),
        )
        conn.commit()
        conn.close()

    def get_listings_by_source(self, source: str) -> list[dict]:
        conn = self._connect()
        cursor = conn.execute("SELECT * FROM Listing WHERE source = ?", (source,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def create_watch(self, data: dict) -> int:
        conn = self._connect()
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        cursor = conn.execute(
            f"INSERT INTO Watch ({columns}) VALUES ({placeholders})",
            list(data.values()),
        )
        conn.commit()
        watch_id = cursor.lastrowid
        conn.close()
        return watch_id

    def get_active_watches(self) -> list[dict]:
        conn = self._connect()
        cursor = conn.execute("SELECT * FROM Watch WHERE active = 1")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_all_watches(self) -> list[dict]:
        conn = self._connect()
        cursor = conn.execute("SELECT * FROM Watch ORDER BY created_at DESC")
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def deactivate_watch(self, watch_id: int) -> None:
        conn = self._connect()
        conn.execute("UPDATE Watch SET active = 0 WHERE id = ?", (watch_id,))
        conn.commit()
        conn.close()

    def activate_watch(self, watch_id: int) -> None:
        conn = self._connect()
        conn.execute("UPDATE Watch SET active = 1 WHERE id = ?", (watch_id,))
        conn.commit()
        conn.close()

    def delete_watch(self, watch_id: int) -> None:
        conn = self._connect()
        conn.execute("DELETE FROM Watch WHERE id = ?", (watch_id,))
        conn.commit()
        conn.close()

    def update_watch_last_checked(self, watch_id: int) -> None:
        conn = self._connect()
        conn.execute(
            "UPDATE Watch SET last_checked = ? WHERE id = ?",
            (datetime.now().isoformat(), watch_id),
        )
        conn.commit()
        conn.close()

    def is_listing_seen(self, listing_id: str, watch_id: int) -> bool:
        conn = self._connect()
        cursor = conn.execute(
            "SELECT 1 FROM SeenListing WHERE listing_id = ? AND watch_id = ?",
            (listing_id, watch_id),
        )
        result = cursor.fetchone() is not None
        conn.close()
        return result

    def mark_listing_seen(self, listing_id: str, watch_id: int) -> None:
        conn = self._connect()
        conn.execute(
            "INSERT OR IGNORE INTO SeenListing (listing_id, watch_id) VALUES (?, ?)",
            (listing_id, watch_id),
        )
        conn.commit()
        conn.close()

    def mark_listing_notified(self, listing_id: str, watch_id: int) -> None:
        conn = self._connect()
        conn.execute(
            "UPDATE SeenListing SET notified = 1 WHERE listing_id = ? AND watch_id = ?",
            (listing_id, watch_id),
        )
        conn.commit()
        conn.close()

    def get_seen_listing(self, listing_id: str, watch_id: int) -> dict | None:
        conn = self._connect()
        cursor = conn.execute(
            "SELECT * FROM SeenListing WHERE listing_id = ? AND watch_id = ?",
            (listing_id, watch_id),
        )
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        result = dict(row)
        result["notified"] = bool(result["notified"])
        return result
