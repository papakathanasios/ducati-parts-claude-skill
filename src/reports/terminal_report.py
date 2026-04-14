from src.core.types import Listing, ConditionScore

SCORE_ICONS = {ConditionScore.GREEN: "G", ConditionScore.YELLOW: "Y", ConditionScore.RED: "R"}


def format_terminal_report(listings: list[Listing], query: str, report_path: str) -> str:
    lines: list[str] = []
    if not listings:
        lines.append(f'Search: "{query}" -- No listings found.')
        lines.append(f"Report: {report_path}")
        return "\n".join(lines)

    green_count = sum(1 for l in listings if l.condition_score == ConditionScore.GREEN)
    yellow_count = sum(1 for l in listings if l.condition_score == ConditionScore.YELLOW)
    red_count = sum(1 for l in listings if l.condition_score == ConditionScore.RED)

    lines.append(f'Search: "{query}" -- {len(listings)} listings found')
    lines.append(f"  Condition: {green_count} green | {yellow_count} yellow | {red_count} red")
    lines.append("")

    top = sorted(listings, key=lambda l: l.total_price)[:3]
    lines.append("Top 3 by price:")
    for i, listing in enumerate(top, 1):
        icon = SCORE_ICONS[listing.condition_score]
        eu_tag = "EU" if listing.is_eu else "non-EU"
        flag = " [!ship]" if listing.shipping_ratio_flag else ""
        lines.append(f"  {i}. [{icon}] {listing.total_price:.2f} EUR total | {listing.source} | {listing.seller_country} ({eu_tag}){flag}")
        lines.append(f"     {listing.title[:70]}")
        lines.append(f"     Part: {listing.part_price:.2f} | Ship: {listing.shipping_price:.2f} | {listing.listing_url}")

    lines.append("")
    lines.append(f"Full report: {report_path}")
    return "\n".join(lines)
