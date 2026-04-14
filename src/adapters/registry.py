import os

from src.adapters.base import BaseAdapter
from src.adapters.ebay import EbayAdapter
from src.adapters.olx import OlxBgAdapter, OlxRoAdapter, OlxPlAdapter
from src.adapters.subito import SubitoAdapter


def build_adapter_registry() -> dict[str, BaseAdapter]:
    adapters: dict[str, BaseAdapter] = {}

    # eBay (API-based, requires credentials)
    ebay_app_id = os.environ.get("EBAY_APP_ID")
    ebay_cert_id = os.environ.get("EBAY_CERT_ID")
    if ebay_app_id and ebay_cert_id:
        adapters["ebay_eu"] = EbayAdapter(app_id=ebay_app_id, cert_id=ebay_cert_id)

    # Tier 1: Cheap Eastern EU
    adapters["olx_bg"] = OlxBgAdapter()
    adapters["olx_ro"] = OlxRoAdapter()
    adapters["olx_pl"] = OlxPlAdapter()

    # Tier 2: Moderate
    adapters["subito_it"] = SubitoAdapter()

    # Additional adapters registered here as they are validated:
    # adapters["allegro"] = AllegroAdapter()
    # adapters["jofogas"] = JofogasAdapter()
    # adapters["bazos_cz"] = BazosCzAdapter()
    # adapters["bazos_sk"] = BazosSkAdapter()
    # adapters["njuskalo"] = NjuskaloAdapter()
    # adapters["bolha"] = BolhaAdapter()
    # adapters["kleinanzeigen"] = KleinanzeigenAdapter()
    # adapters["leboncoin"] = LeboncoinAdapter()
    # adapters["wallapop"] = WallapopAdapter()

    return adapters
