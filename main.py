import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
import requests

# ==========================================
# 1. Setup කොටස
# ==========================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ඔබේ Chat ID එක මෙතනට අලවන්න (උදා: 123456789)
YOUR_CHAT_ID = 123456789  # <--- මෙතනට ඔබේ ඇත්ත ID අංකය අලවන්න!

BINANCE_TICKER_API = "https://api.binance.com/api/v3/ticker/24hr"
BINANCE_PRICE_API = "https://api.binance.com/api/v3/ticker/price"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# 2. Binance Data Functions
# ==========================================

def get_top_gainers(limit=5):
    try:
        response = requests.get(BINANCE_TICKER_API)
        if response.status_code == 200:
            data = response.json()
            usdt_pairs = [x for x in data if x['symbol'].endswith('USDT')]
            sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['priceChangePercent']), reverse=True)
            top_5 = sorted_pairs[:limit]
            symbols = [item['symbol'] for item in top_5]
            return symbols, top_5
        return [], []
    except Exception as e:
        logging.error(f"Binance Error: {e}")
        return [], []

def get_live_prices(symbols):
    try:
        response = requests.get(BINANCE_PRICE_API)
        if response.status_code == 200:
            all_prices = response.json()
            filtered = {item['symbol']: item['price'] for item in all_prices if item['symbol'] in symbols}
            return filtered
        return {}
    except Exception as e:
        logging.error(f"Binance Price Error: {e}")
        return {}

# ==========================================
# 3. Bot Functions
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    owner_name = "Sasith Imarsha"
    bot_birthday = "2026.08.16"
    
    welcome_msg = (
        f"🟢 **සාදරයෙන් පිළිගනිමු!** 🟢\n\n"
        f"මෙම Bot එක නිර්මාණය කරන ලද්දේ **{owner_name}** විසිනි.\n"
        f"මාගේ උපන් දිනය: **{bot_birthday}** 🎂\n\n"
        f"🤖 මම උසස් Elliott Wave + Fibonacci විශ්ලේෂකයෙකි.\n"
        f"📊 සෑම පැය 3කට වරක්ම Top Gainers වාර්තාවක් ලබා දෙමි.\n"
        f"💬 කාසියක නම අමතා විශ්ලේෂණය ලබා ගන්න.\n"
        f"**අලුත් Command:** ඔබේ Chat ID එක දැනගන්න `/myid` ටයිප් කරන්න."
    )
    await update.message.reply_text(welcome_msg)

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"ඔබේ Telegram Chat ID එක: `{update.effective_chat.id}`")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Top Gainers Check
        if "top" in user_message.lower() or "gain" in user_message.lower() or "හොඳම" in user_message.lower():
            await update.message.reply_text("📊 වෙළඳපොලේ Top 5 Gainers සොයමින්...")
            symbols, top_5_data = get_top_gainers(limit=5)
            if not symbols:
                await update.message.reply_text("⚠️ මේ මොහොතේ දත්ත ලබා ගැනීමට නොහැකි විය.")
                return

            prices = get_live_prices(symbols)
            market_data = "\n**📈 TOP 5 GAINERS (LIVE DATA):**\n"
            for sym in symbols:
                pct = next((item['priceChangePercent'] for item in top_5_data if item['symbol'] == sym), "0.00")
                price = prices.get(sym, "0.00")
                market_data += f"• {sym}: ${float(price):,.4f} | +{pct}%\n"

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": """You are a world-class Elliott Wave & Fibonacci specialist.
You MUST reply in 100% Sinhala.
You MUST identify the EXTENDED wave (1, 3, or 5) using this flow:
1. Check Wave 1 first. If extended, use 1st Wave Extended rules.
2. If not, check Wave 3. If extended, use 3rd Wave Extended rules.
3. If not, assume Wave 5 is extended and use 5th Wave Extended rules.

Fibonacci Rules:
1st Wave Ext: W2(23.6,38.2,50,61.8), W3(61.8,78.6), W4(23.6,38.2,50), W5(61.8,78.6)
3rd Wave Ext: W2(38.2,50,61.8,78.6), W3(50,61.8,78.6,100,141.4), W4(23.6,38.2,50,61.8), W5(61.8,100)
5th Wave Ext: W2(38.2,50,61.8,78.6), W3(50,61.8,78.6,100,141.4), W4(23.6,38.2,50,61.8), W5(141.4,161.8)

Provide TP, SL, Support/Resistance and a clear BUY/SELL recommendation."""},
                    {"role": "user", "content": f"{market_data}\nWhich one is the best buy?"}
                ],
                temperature=0.3,
                max_tokens=4096,
            )
            bot_reply = response.choices[0].message.content
            footer = f"\n\n---\n🤖 Developed by: Sasith Imarsha | 🎂 Birthday: 2026.08.16"
            await update.message.reply_text(bot_reply + footer)
            return

        # Normal Coin Analysis
        coin_keywords = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC", "LINK"]
        found_coins = []
        for coin in coin_keywords:
            if coin in user_message.upper():
                found_coins.append(coin)
        
        market_data_text = ""
        if found_coins:
            prices = get_live_prices(found_coins)
            if prices:
                market_data_text = "\n**📈 LIVE MARKET DATA:**\n"
                for symbol, price in prices.items():
                    market_data_text += f"• {symbol}: ${float(price):,.4f}\n"

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": """You are a world-class Elliott Wave & Fibonacci specialist.
You MUST reply in 100% Sinhala.
You MUST identify the EXTENDED wave using the exact logic:
1. Check Wave 1. If extended, use 1st Wave Extended rules.
2. If not, check Wave 3. If extended, use 3rd Wave Extended rules.
3. If not, assume Wave 5 is extended and use 5th Wave Extended rules.

Fibonacci Rules:
1st Wave Ext: W2(23.6,38.2,50,61.8), W3(61.8,78.6), W4(23.6,38.2,50), W5(61.8,78.6)
3rd Wave Ext: W2(38.2,50,61.8,78.6), W3(50,61.8,78.6,100,141.4), W4(23.6,38.2,50,61.8), W5(61.8,100)
5th Wave Ext: W2(38.2,50,61.8,78.6), W3(50,61.8,78.6,100,141.4), W4(23.6,38.2,50,61.8), W5(141.4,161.8)

Provide TP, SL, Support/Resistance and a clear BUY/SELL recommendation."""},
                {"role": "user", "content": f"{market_data_text}\nUser Question: {user_message}"}
            ],
            temperature=0.3,
            max_tokens=2048,
        )
        
        bot_reply = response.choices[0].message.content
        footer = f"\n\n---\n🤖 Developed by: Sasith Imarsha | 🎂 Birthday: 2026.08.16"
        await update.message.reply_text(bot_reply + footer)

    except Exception as e:
        print(f"Error: {e}")
        await asyncio.sleep(1)
        await handle_message(update, context)

# ==========================================
# 4. Scheduler (පැය 3කට වරක්)
# ==========================================

async def scheduled_top_gainers(context: ContextTypes.DEFAULT_TYPE):
    symbols, top_5_data = get_top_gainers(limit=5)
    if not symbols:
        await context.bot.send_message(chat_id=context.job.chat_id, text="⚠️ දත්ත ලබා ගැනීමට අපොහොසත් විය.")
        return

    prices = get_live_prices(symbols)
    market_data = "\n**📊 TOP 5 GAINERS (3-HOUR REPORT):**\n"
    for sym in symbols:
        pct = next((item['priceChangePercent'] for item in top_5_data if item['symbol'] == sym), "0.00")
        price = prices.get(sym, "0.00")
        market_data += f"• {sym}: ${float(price):,.4f} | +{pct}%\n"

    prompt = f"""{market_data}

Which is the best buy among these 5 coins right now?
Analyze the best coin using the exact Elliott Wave & Fibonacci rules (1st, 3rd, or 5th Wave Extended).
Provide TP, SL, Support/Resistance and a clear BUY/SELL recommendation.
100% Sinhala language only."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4096,
        )
        report = response.choices[0].message.content
        footer = f"\n\n---\n🤖 Developed by: Sasith Imarsha | 🎂 Birthday: 2026.08.16"
        await context.bot.send_message(chat_id=context.job.chat_id, text=report + footer)

    except Exception as e:
        await context.bot.send_message(chat_id=context.job.chat_id, text=f"⚠️ Error: {e}")

# ==========================================
# 5. Main Loop
# ==========================================

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", my_id))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(scheduled_top_gainers, interval=10800, first=10, chat_id=YOUR_CHAT_ID)
        logging.info("Scheduled analysis set.")

    print("Bot එක Advanced Wave Logic සමඟ පණ ගැහෙමින් පවතී...")
    application.run_polling(drop_pending_updates=True)