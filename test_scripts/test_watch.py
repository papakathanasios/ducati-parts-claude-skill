import json
from unittest.mock import patch
from src.watch.manager import WatchManager
from src.watch.notifier import send_macos_notification
from src.db.database import Database


def test_watch_manager_create_and_list(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    mgr = WatchManager(db)
    watch_id = mgr.create(query="clutch lever", max_total_price=40.0,
        target_models=["Multistrada 1260 Enduro", "Multistrada 1260"], part_category="controls")
    assert watch_id == 1
    watches = mgr.list_active()
    assert len(watches) == 1
    assert watches[0]["query"] == "clutch lever"


def test_watch_manager_pause_and_resume(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    mgr = WatchManager(db)
    watch_id = mgr.create(query="exhaust", max_total_price=500.0)
    mgr.pause(watch_id)
    assert len(mgr.list_active()) == 0
    mgr.resume(watch_id)
    assert len(mgr.list_active()) == 1


def test_watch_manager_remove(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    mgr = WatchManager(db)
    watch_id = mgr.create(query="lever", max_total_price=30.0)
    mgr.remove(watch_id)
    assert len(mgr.list_all()) == 0


def test_watch_manager_update_budget(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    mgr = WatchManager(db)
    watch_id = mgr.create(query="guard", max_total_price=60.0)
    mgr.update_budget(watch_id, 80.0)
    watches = mgr.list_active()
    assert watches[0]["max_total_price"] == 80.0


def test_macos_notification_command():
    with patch("subprocess.run") as mock_run:
        send_macos_notification(title="Ducati Parts Finder",
            message='3 new listings for "clutch lever"',
            subtitle="Best: 18 EUR total (OLX.bg)")
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "osascript" in cmd[0]
