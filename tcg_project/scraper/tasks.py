from .scraper import scrape_cards
import asyncio

def run_scraper():
    return asyncio.run(scrape_cards())

