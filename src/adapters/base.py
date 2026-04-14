from abc import ABC, abstractmethod
from dataclasses import dataclass
from src.core.types import RawListing, SearchFilters


@dataclass
class AdapterHealthCheck:
    healthy: bool
    message: str


class BaseAdapter(ABC):
    source_name: str
    language: str
    country: str
    currency: str

    @abstractmethod
    async def search(self, query: str, filters: SearchFilters) -> list[RawListing]:
        ...

    @abstractmethod
    async def health_check(self) -> AdapterHealthCheck:
        ...
