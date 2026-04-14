import sqlite3
from pathlib import Path
from src.db.database import Database


def test_database_creates_tables(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.initialize()
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    assert "Listing" in tables
    assert "Watch" in tables
    assert "SeenListing" in tables
    assert "PartsCatalog" in tables


def test_database_insert_and_query_listing(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.initialize()
    db.upsert_listing({
        "id": "ebay_123", "source": "ebay", "title": "Clutch lever",
        "description": "Good condition OEM", "part_price": 25.00,
        "shipping_price": 10.00, "total_price": 35.00,
        "shipping_ratio_flag": False, "currency_original": "EUR",
        "seller_country": "IT", "is_eu": True, "condition_raw": "Good",
        "condition_score": "green", "condition_notes": "Clean",
        "photos": '["https://example.com/p1.jpg"]',
        "listing_url": "https://ebay.it/123",
        "compatible_models": '["Multistrada 1260 Enduro"]',
        "compatibility_confidence": "definite", "oem_part_number": "63040601A",
        "date_listed": "2026-04-10T00:00:00", "date_found": "2026-04-14T00:00:00",
    })
    listings = db.get_listings_by_source("ebay")
    assert len(listings) == 1
    assert listings[0]["id"] == "ebay_123"
    assert listings[0]["part_price"] == 25.00


def test_database_upsert_updates_existing(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.initialize()
    listing_data = {
        "id": "ebay_123", "source": "ebay", "title": "Clutch lever",
        "description": "Good condition", "part_price": 25.00,
        "shipping_price": 10.00, "total_price": 35.00,
        "shipping_ratio_flag": False, "currency_original": "EUR",
        "seller_country": "IT", "is_eu": True, "condition_raw": "Good",
        "condition_score": "green", "condition_notes": "Clean",
        "photos": "[]", "listing_url": "https://ebay.it/123",
        "compatible_models": "[]", "compatibility_confidence": "definite",
        "oem_part_number": "", "date_listed": "2026-04-10T00:00:00",
        "date_found": "2026-04-14T00:00:00",
    }
    db.upsert_listing(listing_data)
    listing_data["part_price"] = 20.00
    listing_data["total_price"] = 30.00
    db.upsert_listing(listing_data)
    listings = db.get_listings_by_source("ebay")
    assert len(listings) == 1
    assert listings[0]["part_price"] == 20.00


def test_watch_crud(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.initialize()
    watch_id = db.create_watch({
        "query": "clutch lever", "part_category": "controls",
        "oem_number": "", "max_total_price": 40.00,
        "target_models": '["Multistrada 1260 Enduro", "Multistrada 1260"]',
        "sources": '["all"]', "active": True,
    })
    assert watch_id == 1
    watches = db.get_active_watches()
    assert len(watches) == 1
    assert watches[0]["query"] == "clutch lever"
    db.deactivate_watch(watch_id)
    watches = db.get_active_watches()
    assert len(watches) == 0


def test_seen_listing_tracking(tmp_path):
    db_path = tmp_path / "test.db"
    db = Database(str(db_path))
    db.initialize()
    watch_id = db.create_watch({
        "query": "test", "part_category": "", "oem_number": "",
        "max_total_price": 100.00, "target_models": "[]",
        "sources": "[]", "active": True,
    })
    assert db.is_listing_seen("ebay_123", watch_id) is False
    db.mark_listing_seen("ebay_123", watch_id)
    assert db.is_listing_seen("ebay_123", watch_id) is True
    db.mark_listing_notified("ebay_123", watch_id)
    seen = db.get_seen_listing("ebay_123", watch_id)
    assert seen["notified"] is True
