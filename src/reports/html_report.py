from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from src.core.types import Listing, ConditionScore

TEMPLATE_DIR = Path(__file__).parent / "templates"


def generate_html_report(listings: list[Listing], query: str, output_path: str) -> None:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
    template = env.get_template("report.html")
    green_count = sum(1 for l in listings if l.condition_score == ConditionScore.GREEN)
    yellow_count = sum(1 for l in listings if l.condition_score == ConditionScore.YELLOW)
    red_count = sum(1 for l in listings if l.condition_score == ConditionScore.RED)
    countries = sorted(set(l.seller_country for l in listings))
    html = template.render(
        query=query, listings=listings, green_count=green_count,
        yellow_count=yellow_count, red_count=red_count,
        countries=countries, generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
