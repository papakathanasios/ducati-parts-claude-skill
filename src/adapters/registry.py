import os

from src.adapters.base import BaseAdapter
from src.adapters.allegro import AllegroAdapter
from src.adapters.bazos import BazosCzAdapter, BazosSkAdapter
from src.adapters.bolha import BolhaAdapter
from src.adapters.ebay import EbayAdapter
from src.adapters.jofogas import JofogasAdapter
from src.adapters.kleinanzeigen import KleinanzeigenAdapter
from src.adapters.leboncoin import LeboncoinAdapter
from src.adapters.njuskalo import NjuskaloAdapter
from src.adapters.olx import OlxBgAdapter, OlxRoAdapter, OlxPlAdapter
from src.adapters.subito import SubitoAdapter
from src.adapters.wallapop import WallapopAdapter


def build_adapter_registry() -> dict[str, BaseAdapter]:
    adapters: dict[str, BaseAdapter] = {}

    # eBay (API-based, requires credentials)
    ebay_app_id = os.environ.get("EBAY_APP_ID")
    ebay_cert_id = os.environ.get("EBAY_CERT_ID")
    if ebay_app_id and ebay_cert_id:
        adapters["ebay_eu"] = EbayAdapter(app_id=ebay_app_id, cert_id=ebay_cert_id)

    # Tier 1: Eastern EU classifieds
    adapters["olx_bg"] = OlxBgAdapter()
    adapters["olx_ro"] = OlxRoAdapter()
    adapters["olx_pl"] = OlxPlAdapter()
    adapters["allegro"] = AllegroAdapter()
    adapters["jofogas"] = JofogasAdapter()
    adapters["bazos_cz"] = BazosCzAdapter()
    adapters["bazos_sk"] = BazosSkAdapter()
    adapters["njuskalo"] = NjuskaloAdapter()
    adapters["bolha"] = BolhaAdapter()

    # Tier 2: Italy + eBay
    adapters["subito_it"] = SubitoAdapter()

    # Tier 3: Western EU
    adapters["kleinanzeigen"] = KleinanzeigenAdapter()
    adapters["leboncoin"] = LeboncoinAdapter()
    adapters["wallapop"] = WallapopAdapter()

    return adapters
