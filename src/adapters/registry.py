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

# Specialist Ducati shops and breakers
from src.adapters.desmomarket import DesmoMarketAdapter
from src.adapters.dgarageparts import DGaragePartsAdapter
from src.adapters.fresiamoto import FresiaMotAdapter
from src.adapters.motoricambi import MotoricambiAdapter
from src.adapters.eramotoricambi import EraMotoRicambiAdapter
from src.adapters.used_italian_parts import UsedItalianPartsAdapter
from src.adapters.ducbikeparts import DucBikePartsAdapter
from src.adapters.motorradteile_hannover import MotorradteileHannoverAdapter
from src.adapters.duc_store import DucStoreAdapter
from src.adapters.ital_allparts import ItalAllpartsAdapter
from src.adapters.forza_moto import ForzaMotoAdapter
from src.adapters.dezosmoto import DezosmotoAdapter
from src.adapters.speckmoto import SpeckMotoAdapter
from src.adapters.motodesguace_ferrer import MotodesguaceFerrerAdapter
from src.adapters.motoye import MotoyeAdapter
from src.adapters.desguaces_pedros import DesguacesPedrosAdapter
from src.adapters.ducatimondo import DucatiMondoAdapter
from src.adapters.motogrotto import MotoGrottoAdapter
from src.adapters.colchester_breakers import ColchesterBreakersAdapter
from src.adapters.cheshire_breakers import CheshireBreakersAdapter
from src.adapters.bmotor import BMotorAdapter
from src.adapters.maleducati import MaleDucatiAdapter
from src.adapters.ducatiparts_cz import DucatiPartsCzAdapter


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

    # Tier 1: Eastern EU specialists
    adapters["bmotor"] = BMotorAdapter()
    adapters["maleducati"] = MaleDucatiAdapter()
    adapters["ducatiparts_cz"] = DucatiPartsCzAdapter()

    # Tier 2: Italy + eBay
    adapters["subito_it"] = SubitoAdapter()
    adapters["desmomarket"] = DesmoMarketAdapter()
    adapters["dgarageparts"] = DGaragePartsAdapter()
    adapters["fresiamoto"] = FresiaMotAdapter()
    adapters["motoricambi"] = MotoricambiAdapter()
    adapters["eramotoricambi"] = EraMotoRicambiAdapter()

    # Tier 3: Western EU classifieds
    adapters["kleinanzeigen"] = KleinanzeigenAdapter()
    adapters["leboncoin"] = LeboncoinAdapter()
    adapters["wallapop"] = WallapopAdapter()

    # Tier 3: Western EU specialists
    adapters["used_italian_parts"] = UsedItalianPartsAdapter()
    adapters["ducbikeparts"] = DucBikePartsAdapter()
    adapters["motorradteile_hannover"] = MotorradteileHannoverAdapter()
    adapters["duc_store"] = DucStoreAdapter()
    adapters["ital_allparts"] = ItalAllpartsAdapter()
    adapters["forza_moto"] = ForzaMotoAdapter()
    adapters["dezosmoto"] = DezosmotoAdapter()
    adapters["speckmoto"] = SpeckMotoAdapter()
    adapters["motodesguace_ferrer"] = MotodesguaceFerrerAdapter()
    adapters["motoye"] = MotoyeAdapter()
    adapters["desguaces_pedros"] = DesguacesPedrosAdapter()

    # Tier 3: UK specialists
    adapters["ducatimondo"] = DucatiMondoAdapter()
    adapters["motogrotto"] = MotoGrottoAdapter()
    adapters["colchester_breakers"] = ColchesterBreakersAdapter()
    adapters["cheshire_breakers"] = CheshireBreakersAdapter()

    return adapters
