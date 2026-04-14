from decimal import Decimal

EU_COUNTRIES = frozenset({
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR",
    "DE", "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL",
    "PL", "PT", "RO", "SK", "SI", "ES", "SE",
})

SHIPPING_RANGES: dict[str, tuple[int, int]] = {
    "BG": (5, 10), "RO": (6, 12), "HR": (8, 15), "SI": (10, 16),
    "HU": (10, 18), "IT": (8, 15), "PL": (12, 22), "CZ": (14, 22),
    "SK": (12, 20), "DE": (10, 20), "FR": (12, 22), "ES": (12, 25),
    "AT": (10, 18), "NL": (12, 20), "BE": (12, 20), "GB": (15, 30),
}
DEFAULT_RANGE = (15, 30)


class ShippingEstimator:
    def __init__(self, destination_postal: str, destination_country: str):
        self.destination_postal = destination_postal
        self.destination_country = destination_country

    def estimate(self, seller_country: str) -> tuple[Decimal, Decimal]:
        low, high = SHIPPING_RANGES.get(seller_country.upper(), DEFAULT_RANGE)
        return Decimal(str(low)), Decimal(str(high))

    def midpoint(self, seller_country: str) -> Decimal:
        low, high = self.estimate(seller_country)
        return (low + high) / 2

    def is_eu(self, country_code: str) -> bool:
        return country_code.upper() in EU_COUNTRIES
