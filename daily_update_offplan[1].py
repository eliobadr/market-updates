#!/usr/bin/env python3
"""
Daily Abu Dhabi & Dubai OFF-PLAN real estate update bot.

What it does:
1. Asks Claude (with live web search) to research today's news on new project
   launches, off-plan sales activity, payment plans, and developer announcements.
2. Formats the result into a clean daily briefing.
3. Sends it to you on Telegram.

Run manually:
    python daily_update_offplan.py

Run automatically:
    See .github/workflows/daily-update-offplan.yml (runs once a day via GitHub Actions)

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

PROMPT = """You are an off-plan real estate analyst for a property investor focused on
Abu Dhabi and Dubai. Research TODAY's news (use web search) and produce a concise
daily OFF-PLAN market briefing with these sections:

1. NEW PROJECT LAUNCHES
   - Any newly announced or newly launched off-plan/pre-construction projects
   - Developer name, project name, area, and building type (villas/apartments/
     townhouses/branded residences)
   - Starting prices or price-per-sqft if reported

2. DEVELOPER & PAYMENT PLAN NEWS
   - Announcements from major developers (Emaar, Aldar, DAMAC, Nakheel, Sobha,
     Meraas, Dubai Holding, Modon, Q Properties, Ellington, Binghatti, Azizi,
     Danube, Deyaar, Arada, IMKAN, and other active developers)
   - New or changed payment plans (e.g. post-handover plans, 1% monthly schemes)
   - Handover date announcements or delays for major projects

3. OFF-PLAN SALES ACTIVITY & DEMAND SIGNALS
   - Reported off-plan transaction volumes vs secondary, sell-out speed of
     launches, waitlists/oversubscription, broker commentary on off-plan demand
   - Any DLD data specifically breaking out off-plan vs ready transactions

4. BRANDED RESIDENCES & MEGA-PROJECTS
   - Updates on branded residence launches (hotel-branded, celebrity-branded)
   - Progress on giga-projects (e.g. Dubai Creek Harbour, Palm Jebel Ali,
     Saadiyat Island phases, Yas Island phases, Expo City developments)

5. REGULATORY CHANGES AFFECTING OFF-PLAN BUYERS
   - Escrow law changes, RERA/DLD rules on off-plan sales, oqood registration
     changes, developer licensing news

For each item give:
- A short bold headline
- 1-3 sentence summary in your own words (no long quotes)
- The specific area/community (e.g. Yas Island, Dubai South, JVC, Dubai Hills,
  Saadiyat Island, Business Bay, Dubai Creek Harbour)
- The source name (e.g. "The National", "Gulf News", "Zawya", "Property Finder",
  "Arabian Business")

If there is genuinely little news on a section today, say so briefly rather than
padding it. Do not include secondary-market resale transactions or general rental
market commentary — this briefing is off-plan only. Keep the whole briefing
skimmable in under 2 minutes. Use plain text formatting suitable for a Telegram
message: short lines, simple dashes for bullets, no markdown tables. Do not use
asterisks for bold (Telegram plain text). Start with today's date and the label
"OFF-PLAN MARKET UPDATE" as a heading.
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
