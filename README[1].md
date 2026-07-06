# Daily Abu Dhabi & Dubai Real Estate Update Bots

Sends you two separate daily Telegram messages, researched live by Claude with
web search:

1. **Off-plan update** (`daily_update_offplan.py`) — new project launches,
   developer/payment plan news, off-plan sales activity, branded residences,
   escrow/regulatory news for pre-construction buyers.
2. **Secondary market update** (`daily_update_secondary.py`) — resale
   transactions, price index data, rental market, supply/inventory, buyer/seller
   dynamics, and regulation affecting existing property owners.

## How it works
Every day, each script asks Claude to search the web for that day's news in its
category, summarizes it, and sends it to your Telegram as its own message. Both
run automatically via GitHub Actions (free), so your computer doesn't need to
be on. They're staggered 15 minutes apart (9:00am and 9:15am Gulf time by
default) so the two messages don't land at the same moment.

---

## Setup (about 10 minutes)

### 1. Create your Telegram bot
1. Open Telegram, search for **@BotFather**, and start a chat.
2. Send `/newbot`, give it a name and a username (must end in `bot`).
3. BotFather gives you a **token** like `123456789:ABCdefGhIJKlmNoPQRstuVWxyz`.
   Save it — this is your `TELEGRAM_BOT_TOKEN`.
4. Start a chat with your new bot (search its username, click Start, send it
   any message, e.g. "hi").

### 2. Get your Telegram chat ID
1. In your browser, visit (replace `<TOKEN>` with your bot token):
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
2. Look for `"chat":{"id":123456789,...}` in the response — that number is
   your `TELEGRAM_CHAT_ID`.
   (If you see an empty result, make sure you sent the bot a message first,
   then refresh.)

### 3. Get an Anthropic API key
1. Go to https://console.anthropic.com, create/sign in to an account.
2. Go to **API Keys** and create a new key. This is your `ANTHROPIC_API_KEY`.
   Note: this is billed separately from any Claude.ai subscription — API
   usage is pay-as-you-go (typically a few cents per day for this task).

### 4. Put the code on GitHub
1. Create a new **private** GitHub repository (e.g. `uae-market-bot`).
2. Upload all files from this folder, keeping the `.github/workflows/`
   folder structure intact.

### 5. Add your secrets to GitHub
In your repo: **Settings → Secrets and variables → Actions → New repository
secret**. Add these three, one at a time:
- `ANTHROPIC_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### 6. Test it
Go to the **Actions** tab in your repo. You'll see two workflows:
**Daily Off-Plan Market Update** and **Daily Secondary Market Update**. Click
each one → **Run workflow** (this triggers it manually right now, instead of
waiting for the schedule). Check Telegram within a minute or two — you should
get both briefings as separate messages.

That's it. They'll now run automatically every day at the times set in
`.github/workflows/daily-update-offplan.yml` and
`.github/workflows/daily-update-secondary.yml` (default: 9:00am and 9:15am
Gulf time — edit the cron line in either file if you want different hours, or
want the two combined into a single message time).

---

## Running it locally instead (optional)
If you'd rather run it on your own machine/server instead of GitHub Actions:

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
export TELEGRAM_BOT_TOKEN="123456789:ABC..."
export TELEGRAM_CHAT_ID="123456789"
python daily_update_offplan.py
python daily_update_secondary.py
```

To run them daily, add both to your crontab (`crontab -e`):
```
0 9  * * * cd /path/to/uae-market-bot && /usr/bin/python3 daily_update_offplan.py >> log.txt 2>&1
15 9 * * * cd /path/to/uae-market-bot && /usr/bin/python3 daily_update_secondary.py >> log.txt 2>&1
```

---

## Customizing what it looks for
Open `daily_update_offplan.py` or `daily_update_secondary.py` and edit the
`PROMPT` variable near the top of each — you can:
- Add specific developers/projects/areas you personally track
- Ask for a section on interest rates, tourism numbers, or specific
  communities (e.g. Yas Island, Dubai South, JVC)
- Change the tone/length
- Merge the two back into one message by combining both PROMPT sections into
  a single script if you'd rather get one message instead of two

## Cost
- Anthropic API: roughly $0.01–0.05 per day for this prompt size (model:
  `claude-sonnet-4-6`). Set a monthly budget/limit in the Anthropic console
  if you want a hard cap.
- Telegram Bot API: free.
- GitHub Actions: free for this usage level on a personal account.
