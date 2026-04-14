import os
from decimal import Decimal
from datetime import datetime
from src.reports.html_report import generate_html_report
from src.core.types import Listing, ConditionScore, CompatibilityConfidence


def _make_listing(id, price, shipping, source, score):
    return Listing(
        id=id, source=source, title=f"Clutch lever from {source}",
        description="Good condition, OEM part",
        part_price=Decimal(str(price)), shipping_price=Decimal(str(shipping)),
        currency_original="EUR", seller_country="BG", is_eu=True,
        condition_raw="Good", condition_score=score,
        condition_notes="Looks clean in photos",
        photos=["https://example.com/photo1.jpg"],
        listing_url=f"https://{source}.com/{id}",
        compatible_models=["Multistrada 1260 Enduro", "Multistrada 1260"],
        compatibility_confidence=CompatibilityConfidence.DEFINITE,
        oem_part_number="63040601A",
        date_listed=datetime(2026, 4, 10), date_found=datetime(2026, 4, 14))


def test_generate_html_report_creates_file(tmp_path):
    listings = [
        _make_listing("1", 10, 5, "olx_bg", ConditionScore.GREEN),
        _make_listing("2", 20, 8, "subito", ConditionScore.YELLOW),
    ]
    report_path = str(tmp_path / "report.html")
    generate_html_report(listings, query="clutch lever", output_path=report_path)
    assert os.path.exists(report_path)
    with open(report_path) as f:
        html = f.read()
    assert "clutch lever" in html.lower()
    assert "olx_bg" in html
    assert "15.00" in html
    assert "63040601A" in html
    assert "Multistrada 1260 Enduro" in html
    assert "photo1.jpg" in html


def test_generate_html_report_empty(tmp_path):
    report_path = str(tmp_path / "empty.html")
    generate_html_report([], query="exhaust", output_path=report_path)
    assert os.path.exists(report_path)
    with open(report_path) as f:
        html = f.read()
    assert "no listings" in html.lower() or "0 listings" in html.lower()
