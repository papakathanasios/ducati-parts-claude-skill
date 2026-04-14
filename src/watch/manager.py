import json
from src.db.database import Database


class WatchManager:
    def __init__(self, db: Database):
        self.db = db

    def create(
        self,
        query: str,
        max_total_price: float,
        target_models: list[str] | None = None,
        sources: list[str] | None = None,
        part_category: str = "",
        oem_number: str = "",
    ) -> int:
        data = {
            "query": query,
            "max_total_price": max_total_price,
            "part_category": part_category,
            "oem_number": oem_number,
            "target_models": json.dumps(target_models or []),
            "sources": json.dumps(sources or []),
            "active": 1,
        }
        return self.db.create_watch(data)

    def list_active(self) -> list[dict]:
        watches = self.db.get_active_watches()
        return [self._deserialize(w) for w in watches]

    def list_all(self) -> list[dict]:
        watches = self.db.get_all_watches()
        return [self._deserialize(w) for w in watches]

    def pause(self, watch_id: int) -> None:
        self.db.deactivate_watch(watch_id)

    def resume(self, watch_id: int) -> None:
        self.db.activate_watch(watch_id)

    def remove(self, watch_id: int) -> None:
        self.db.delete_watch(watch_id)

    def update_budget(self, watch_id: int, max_total_price: float) -> None:
        self.db.update_watch_budget(watch_id, max_total_price)

    @staticmethod
    def _deserialize(watch: dict) -> dict:
        result = dict(watch)
        for field in ("target_models", "sources"):
            if isinstance(result.get(field), str):
                result[field] = json.loads(result[field])
        return result
