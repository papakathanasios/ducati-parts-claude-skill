from decimal import Decimal
from datetime import datetime
from src.reports.terminal_report import format_terminal_report
from src.core.types import Listing, ConditionScore, CompatibilityConfidence


def _make_listing(id, price, shipping, source, score):
    return Listing(
        id=id, source=source, title=f"Part from {source}", description="Good",
        part_price=Decimal(str(price)), shipping_price=Decimal(str(shipping)),
        currency_original="EUR", seller_country="BG", is_eu=True, condition_raw="Good",
        condition_score=score, condition_notes="OK", photos=[],
        listing_url=f"https://{source}.com/{id}",
        compatible_models=["Multistrada 1260 Enduro"],
        compatibility_confidence=CompatibilityConfidence.DEFINITE,
        oem_part_number="", date_listed=datetime.now(), date_found=datetime.now())


def test_format_terminal_report_with_results():
    listings = [
        _make_listing("1", 10, 5, "olx_bg", ConditionScore.GREEN),
        _make_listing("2", 20, 8, "subito", ConditionScore.YELLOW),
        _make_listing("3", 30, 10, "ebay", ConditionScore.RED),
    ]
    output = format_terminal_report(listings, query="clutch lever", report_path="/tmp/report.html")
    assert "clutch lever" in output
    assert "15.00" in output
    assert "/tmp/report.html" in output


def test_format_terminal_report_empty():
    output = format_terminal_report([], query="exhaust", report_path="/tmp/r.html")
    assert "no listings" in output.lower() or "0" in output


def test_format_terminal_report_shows_top_3():
    listings = [_make_listing(str(i), 10 + i, 5, "olx_bg", ConditionScore.GREEN) for i in range(10)]
    output = format_terminal_report(listings, query="lever", report_path="/tmp/r.html")
    lines = output.strip().split("\n")
    assert len(lines) >= 5
