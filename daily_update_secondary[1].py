#!/usr/bin/env python3
"""
Daily Abu Dhabi & Dubai SECONDARY (resale) real estate update bot.

What it does:
1. Asks Claude (with live web search) to research today's news on resale
   transactions, price index moves, rental market trends, and regulatory
   news relevant to existing/ready properties.
2. Formats the result into a clean daily briefing.
3. Sends it to you on Telegram.

Run manually:
    python daily_update_secondary.py

Run automatically:
    See .github/workflows/daily-update-secondary.yml (runs once a day via GitHub Actions)

Required environment variables (set as GitHub Actions "Secrets", or in a local .env):
    ANTHROPIC_API_KEY   - from https://console.anthropic.com
    TELEGRAM_BOT_TOKEN  - from @BotFather on Telegram
    TELEGRAM_CHAT_ID    - your personal chat id (see README for how to get it)
"""

import os
import sys
import datetime
import requests

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

ANTHROPIC_MODEL = "claude-sonnet-4-6"  # good balance of quality/cost for this task

PROMPT = """You are a secondary (resale) real estate market analyst for a property
investor focused on Abu Dhabi and Dubai. Research TODAY's news (use web search) and
produce a concise daily SECONDARY MARKET briefing with these sections:

1. RESALE TRANSACTIONS & PRICE DATA
   - Notable ready-property resale transactions, price index movements (DLD
     transaction data, Property Finder / Bayut / Reidin / Knight Frank / CBRE /
     ValuStrat indices), price-per-sqft trends by area
   - Any records broken (highest resale, most transactions in a period, etc.)
   - Explicitly note if a data point is off-plan rather than secondary and exclude
     it, or flag clearly if the source doesn't separate the two

2. RENTAL MARKET
   - Rental price trends and yield changes, RERA/DLD rental index updates
   - Notable tenant/landlord disputes, Ejari-related news, rent cap discussions

3. SUPPLY & INVENTORY
   - Ready/existing housing stock levels, vacancy rates, absorption rates
   - Areas seeing rising or falling resale supply

4. BUYER/SELLER MARKET DYNAMICS
   - Mortgage rate changes and financing news affecting resale buyers
   - Broker/agency commentary on resale demand, days-on-market trends
   - Foreign buyer activity in the secondary market

5. REGULATORY CHANGES AFFECTING EXISTING PROPERTY OWNERS
   - Service charge/OA (owners association) regulation, DLD/RERA rule changes
     for resale transactions, property management law updates
   - Golden visa or ownership rule changes relevant to existing property owners

For each item give:
- A short bold headline
- 1-3 sentence summary in your own words (no long quotes)
- The specific area/community (e.g. Yas Island, Dubai South, JVC, Dubai Hills,
  Saadiyat Island, Business Bay, Downtown Dubai, Arabian Ranches)
- The source name (e.g. "The National", "Gulf News", "Zawya", "Property Finder",
  "Arabian Business")

If there is genuinely little news on a section today, say so briefly rather than
padding it. Do not include off-plan/pre-construction project launches — this
briefing is secondary/resale market only. Keep the whole briefing skimmable in
under 2 minutes. Use plain text formatting suitable for a Telegram message: short
lines, simple dashes for bullets, no markdown tables. Do not use asterisks for
bold (Telegram plain text). Start with today's date and the label "SECONDARY
MARKET UPDATE" as a heading.
"""


def get_market_update() -> str:
    if not ANTHROPIC_API_KEY:
        sys.exit("ERROR: ANTHROPIC_API_KEY environment variable is not set.")

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": PROMPT}],
            "tools": [{"type": "web_search_20250305", "name": "web_search"}],
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()

    # Concatenate all text blocks (there can be multiple if the model searched
    # more than once between writing text).
    text_parts = [block["text"] for block in data.get("content", []) if block.get("type") == "text"]
    text = "\n".join(text_parts).strip()

    if not text:
        text = "No update could be generated today (empty response from model)."
    return text


def send_telegram_message(text: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        sys.exit("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variable is not set.")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Telegram messages are capped at 4096 characters; split into chunks if needed.
    max_len = 4000
    chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)] or [text]

    for chunk in chunks:
        resp = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": chunk},
            timeout=30,
        )
        if not resp.ok:
            print(f"Telegram API error: {resp.status_code} {resp.text}", file=sys.stderr)
            resp.raise_for_status()


def main():
    today = datetime.date.today().isoformat()
    print(f"[{today}] Generating market update...")
    update_text = get_market_update()
    print("[+] Update generated, sending to Telegram...")
    send_telegram_message(update_text)
    print("[+] Done.")


if __name__ == "__main__":
    main()
