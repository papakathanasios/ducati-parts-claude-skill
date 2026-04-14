from src.adapters.olx import OlxBgAdapter, OlxRoAdapter, OlxPlAdapter


def test_olx_bg_search_url():
    adapter = OlxBgAdapter()
    url = adapter._build_search_url("лост съединител мултистрада")
    assert "olx.bg" in url
    assert "мултистрада" in url or "search" in url


def test_olx_ro_search_url():
    adapter = OlxRoAdapter()
    url = adapter._build_search_url("maneta ambreiaj multistrada")
    assert "olx.ro" in url


def test_olx_pl_search_url():
    adapter = OlxPlAdapter()
    url = adapter._build_search_url("dzwignia sprzegla multistrada")
    assert "olx.pl" in url


def test_olx_bg_properties():
    adapter = OlxBgAdapter()
    assert adapter.source_name == "olx_bg"
    assert adapter.country == "BG"
    assert adapter.currency == "BGN"


def test_olx_ro_properties():
    adapter = OlxRoAdapter()
    assert adapter.source_name == "olx_ro"
    assert adapter.country == "RO"
    assert adapter.currency == "RON"


def test_olx_pl_properties():
    adapter = OlxPlAdapter()
    assert adapter.source_name == "olx_pl"
    assert adapter.country == "PL"
    assert adapter.currency == "PLN"


def test_olx_bg_language():
    adapter = OlxBgAdapter()
    assert adapter.language == "bg"


def test_olx_ro_language():
    adapter = OlxRoAdapter()
    assert adapter.language == "ro"


def test_olx_pl_language():
    adapter = OlxPlAdapter()
    assert adapter.language == "pl"


def test_olx_bg_base_url():
    adapter = OlxBgAdapter()
    assert adapter.base_url == "https://www.olx.bg"


def test_olx_ro_base_url():
    adapter = OlxRoAdapter()
    assert adapter.base_url == "https://www.olx.ro"


def test_olx_pl_base_url():
    adapter = OlxPlAdapter()
    assert adapter.base_url == "https://www.olx.pl"


def test_olx_bg_url_path_format():
    adapter = OlxBgAdapter()
    url = adapter._build_search_url("ducati")
    assert "/ads/q-ducati/" in url


def test_olx_ro_url_path_format():
    adapter = OlxRoAdapter()
    url = adapter._build_search_url("ducati")
    assert "/oferte/q-ducati/" in url


def test_olx_pl_url_path_format():
    adapter = OlxPlAdapter()
    url = adapter._build_search_url("ducati")
    assert "/oferty/q-ducati/" in url


def test_olx_search_url_encodes_spaces():
    adapter = OlxBgAdapter()
    url = adapter._build_search_url("clutch lever")
    assert "/ads/q-clutch-lever/" in url
