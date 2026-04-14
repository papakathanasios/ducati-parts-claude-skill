from src.core.types import Listing


def deduplicate(listings: list[Listing]) -> list[Listing]:
    seen_ids: set[str] = set()
    unique: list[Listing] = []
    for listing in listings:
        if listing.id not in seen_ids:
            seen_ids.add(listing.id)
            unique.append(listing)
    return unique
