"""
Telegram Bot — Personal Assistant
===================================
Commands:
    /start      - Bot start karo
    /help       - Sab commands dekho
    /weather    - Kisi city ka weather
    /remind     - Reminder set karo (e.g. /remind 10 Paani peeyo)
    /news       - Latest tech news
    /calc       - Calculator (e.g. /calc 25 * 4)
    /joke       - Random joke
    /myid       - Apna Telegram ID dekho

Setup:
    1. @BotFather se bot banao → TOKEN lo
    2. .env mein TOKEN aur API keys daalo
    3. pip install -r requirements.txt
    4. python bot.py
"""

# Auto-install — pehle libraries check aur install karo
from auto_install import setup
setup()

import os
import logging
import requests
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

TOKEN        = os.getenv("TELEGRAM_TOKEN")
WEATHER_KEY  = os.getenv("OPENWEATHER_KEY")   # openweathermap.org — free
NEWS_KEY     = os.getenv("NEWSAPI_KEY")        # newsapi.org — free


# ── /start ─────────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"Namaste {name}! Main tera personal Telegram bot hoon.\n\n"
        "Kya karna chahte ho? /help likh ke sab commands dekho."
    )


# ── /help ──────────────────────────────────────────────────────────────────────
async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "Ye commands use kar sakta hai:\n\n"
        "/weather Delhi       — Kisi bhi city ka weather\n"
        "/remind 15 Chai peeyo — X minutes baad reminder\n"
        "/news                — Latest tech news\n"
        "/calc 200 * 12 / 4   — Calculator\n"
        "/joke                — Ek random joke\n"
        "/myid                — Tera Telegram user ID\n"
    )
    await update.message.reply_text(text)


# ── /myid ──────────────────────────────────────────────────────────────────────
async def myid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(f"Tera Telegram ID: `{uid}`", parse_mode="Markdown")


# ── /weather ───────────────────────────────────────────────────────────────────
async def weather(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text("City ka naam bhi likho.\nExample: /weather Mumbai")
        return

    if not WEATHER_KEY:
        await update.message.reply_text(
            "OPENWEATHER_KEY .env mein nahi hai.\n"
            "openweathermap.org pe free account banao aur key daalo."
        )
        return

    city = " ".join(ctx.args)
    url  = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={WEATHER_KEY}&units=metric&lang=en"
    )

    try:
        resp = requests.get(url, timeout=8)
        if resp.status_code == 404:
            await update.message.reply_text(f"'{city}' nahi mili. City ka naam check karo.")
            return
        resp.raise_for_status()
        data = resp.json()

        desc    = data["weather"][0]["description"].capitalize()
        temp    = data["main"]["temp"]
        feels   = data["main"]["feels_like"]
        humid   = data["main"]["humidity"]
        wind    = data["wind"]["speed"]
        country = data["sys"]["country"]

        msg = (
            f"Weather — {city.title()}, {country}\n\n"
            f"Condition : {desc}\n"
            f"Temp      : {temp}°C (feels like {feels}°C)\n"
            f"Humidity  : {humid}%\n"
            f"Wind      : {wind} m/s"
        )
        await update.message.reply_text(msg)

    except requests.RequestException as e:
        log.error(f"Weather API error: {e}")
        await update.message.reply_text("Weather fetch nahi hua. Baad mein try karo.")


# ── /remind ────────────────────────────────────────────────────────────────────
async def remind(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        await update.message.reply_text(
            "Format: /remind <minutes> <message>\n"
            "Example: /remind 10 Paani peeyo"
        )
        return

    try:
        minutes = int(ctx.args[0])
        if minutes <= 0 or minutes > 1440:
            await update.message.reply_text("Minutes 1 se 1440 ke beech hone chahiye.")
            return
    except ValueError:
        await update.message.reply_text("Pehla argument number hona chahiye.\nExample: /remind 10 Paani peeyo")
        return

    reminder_text = " ".join(ctx.args[1:])
    chat_id       = update.effective_chat.id
    fire_at       = datetime.now() + timedelta(minutes=minutes)

    await update.message.reply_text(
        f"Reminder set ho gaya!\n"
        f"Waqt: {fire_at.strftime('%H:%M:%S')}\n"
        f"Message: {reminder_text}"
    )

    async def send_reminder():
        await asyncio.sleep(minutes * 60)
        await ctx.bot.send_message(
            chat_id=chat_id,
            text=f"Reminder: {reminder_text}"
        )

    asyncio.create_task(send_reminder())


# ── /news ──────────────────────────────────────────────────────────────────────
async def news(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not NEWS_KEY:
        await update.message.reply_text(
            "NEWSAPI_KEY .env mein nahi hai.\n"
            "newsapi.org pe free account banao aur key daalo."
        )
        return

    topic = " ".join(ctx.args) if ctx.args else "technology"
    url   = (
        f"https://newsapi.org/v2/top-headlines"
        f"?q={topic}&language=en&pageSize=5&apiKey={NEWS_KEY}"
    )

    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        articles = resp.json().get("articles", [])

        if not articles:
            await update.message.reply_text(f"'{topic}' ke baare mein abhi koi news nahi mili.")
            return

        lines = [f"Latest news — {topic.title()}\n"]
        for i, a in enumerate(articles[:5], 1):
            title  = a.get("title", "No title")
            source = a.get("source", {}).get("name", "")
            link   = a.get("url", "")
            lines.append(f"{i}. {title}\n   {source} — {link}\n")

        await update.message.reply_text("\n".join(lines), disable_web_page_preview=True)

    except requests.RequestException as e:
        log.error(f"News API error: {e}")
        await update.message.reply_text("News fetch nahi hua. Baad mein try karo.")


# ── /calc ──────────────────────────────────────────────────────────────────────
async def calc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        await update.message.reply_text(
            "Expression likho.\nExample: /calc 25 * 4 + 10"
        )
        return

    expr = " ".join(ctx.args)

    # Sirf safe characters allow karo
    allowed = set("0123456789+-*/().% ")
    if not all(c in allowed for c in expr):
        await update.message.reply_text("Sirf numbers aur +  -  *  /  ()  % use karo.")
        return

    try:
        result = eval(expr, {"__builtins__": {}})  # noqa: S307
        await update.message.reply_text(f"{expr} = {round(result, 6)}")
    except ZeroDivisionError:
        await update.message.reply_text("Zero se divide nahi kar sakte!")
    except Exception:
        await update.message.reply_text("Expression galat hai. Check karo.")


# ── /joke ──────────────────────────────────────────────────────────────────────
async def joke(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        resp = requests.get(
            "https://official-joke-api.appspot.com/random_joke",
            timeout=6
        )
        resp.raise_for_status()
        data  = resp.json()
        setup = data.get("setup", "")
        punch = data.get("punchline", "")
        await update.message.reply_text(f"{setup}\n\n...{punch}")
    except Exception:
        await update.message.reply_text("Joke nahi aaya. Baad mein try karo.")


# ── Unknown command ────────────────────────────────────────────────────────────
async def unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ye command nahi pata. /help likh ke available commands dekho."
    )


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    if not TOKEN:
        raise ValueError("TELEGRAM_TOKEN .env mein nahi hai! Pehle set karo.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("help",    help_cmd))
    app.add_handler(CommandHandler("myid",    myid))
    app.add_handler(CommandHandler("weather", weather))
    app.add_handler(CommandHandler("remind",  remind))
    app.add_handler(CommandHandler("news",    news))
    app.add_handler(CommandHandler("calc",    calc))
    app.add_handler(CommandHandler("joke",    joke))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    log.info("Bot chal raha hai — Ctrl+C se band karo")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
