"""Bolha.com adapter – Slovenian classifieds marketplace.

Uses the same Styria Media Group platform as Njuskalo.hr.
"""

from urllib.parse import quote

from src.adapters.njuskalo import _StyriaPlatformBase


class BolhaAdapter(_StyriaPlatformBase):
    source_name = "bolha"
    language = "sl"
    country = "SI"
    currency = "EUR"
    base_url = "https://www.bolha.com"

    def _build_search_url(self, query: str) -> str:
        return f"{self.base_url}/search/?keywords={quote(query)}"
