from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from xml.etree import ElementTree
import logging

import httpx

logger = logging.getLogger(__name__)

ECB_RATES_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
ECB_NS = {"gesmes": "http://www.gesmes.org/xml/2002-08-01", "eurofxref": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}

_CACHE_DURATION = timedelta(hours=24)


class CurrencyConverter:
    def __init__(self):
        self._rates: dict[str, Decimal] = {}
        self._rates_fetched_at: datetime | None = None
        self._rates_available: bool = False

    def rates_are_fresh(self) -> bool:
        if self._rates_fetched_at is None:
            return False
        return datetime.now(timezone.utc) - self._rates_fetched_at < _CACHE_DURATION

    async def fetch_rates(self) -> None:
        if self.rates_are_fresh():
            return
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(ECB_RATES_URL, timeout=10)
                resp.raise_for_status()
            root = ElementTree.fromstring(resp.text)
            cube = root.find(".//eurofxref:Cube/eurofxref:Cube", ECB_NS)
            if cube is None:
                raise RuntimeError("Failed to parse ECB rate data")
            self._rates = {}
            for rate_elem in cube.findall("eurofxref:Cube", ECB_NS):
                currency = rate_elem.attrib["currency"]
                rate = Decimal(rate_elem.attrib["rate"])
                self._rates[currency] = rate
            self._rates_fetched_at = datetime.now(timezone.utc)
            self._rates_available = True
        except Exception:
            logger.warning("Failed to fetch ECB rates", exc_info=True)
            self._rates_available = False

    def convert(self, amount: Decimal, from_currency: str) -> Decimal:
        from_currency = from_currency.upper()
        if from_currency == "EUR":
            return amount
        if from_currency not in self._rates:
            raise KeyError(f"Unsupported currency: {from_currency}")
        rate = self._rates[from_currency]
        eur_amount = amount / rate
        return eur_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def is_supported(self, currency: str) -> bool:
        return currency.upper() == "EUR" or currency.upper() in self._rates
