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

BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# 2. Binance Data Function
# ==========================================

def get_live_prices(symbols):
    """Binance API එකෙන් අදාළ කාසිවල ලයිව් මිල ගණන් ලබා ගන්න"""
    try:
        response = requests.get(BINANCE_API_URL)
        if response.status_code == 200:
            all_prices = response.json()
            filtered = {item['symbol']: item['price'] for item in all_prices if item['symbol'] in symbols}
            return filtered
        return None
    except Exception as e:
        logging.error(f"Binance API Error: {e}")
        return None

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
        f"🤖 මම උසස් ක්‍රිප්ටෝ වෙළඳ විශ්ලේෂකයෙකි.\n"
        f"📊 Binance වෙතින් සජීවී මිල ගණන් ලබාගෙන මම විශ්ලේෂණය කරමි.\n"
        f"💬 ඔබට ඕනෑම කාසියක නමක් අමතා ප්‍රශ්න ඇසිය හැක (උදා: BTC, ETH, SOL).\n"
        f"⏰ මම සෑම පැය 3කට වරක්ම Top 10 කාසි වල වාර්තාවක් ඔබට යවමි.\n\n"
        f"**අලුත් Command:** ඔබේ Chat ID එක දැනගන්න `/myid` ටයිප් කරන්න."
    )
    await update.message.reply_text(welcome_msg)

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"ඔබේ Telegram Chat ID එක: `{update.effective_chat.id}`")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Coin හඳුනාගැනීම
        coin_keywords = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC", "LINK"]
        found_coins = []
        for coin in coin_keywords:
            if coin in user_message.upper():
                found_coins.append(coin)
        
        market_data_text = ""
        if found_coins:
            prices = get_live_prices(found_coins)
            if prices:
                market_data_text = "\n**📈 LIVE MARKET DATA (BASE YOUR CALCULATIONS ON THIS):**\n"
                for symbol, price in prices.items():
                    market_data_text += f"• {symbol}: ${float(price):,.4f}\n"
                market_data_text += "\n**⚠️ REQUIREMENT:** Base ALL your Fibonacci, TP, SL, and Elliott Wave analysis strictly on these exact prices.\n"
            else:
                market_data_text = "\n*(⚠️ LIVE DATA UNAVAILABLE. Analysis may be inaccurate.)*\n\n"

        # Groq AI Request (Elliott Wave + Zigzag + Fib)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"""You are a world-class Elliott Wave, Fibonacci, and Technical Analyst, exactly like a professional TradingView analyst.
You MUST reply in 100% pure Sinhala language.

Analyze the coin based on the Live Price provided below.
Provide a detailed report with the following EXACT sections:

1. **Main Trend Identification:**
   - Clearly mark the Main Trend (Uptrend or Downtrend).
   - Identify the current position in the Elliott Wave cycle (Wave 1, 2, 3, 4, or 5).
   - Break down the structure specifically focusing on **Wave 5**.

2. **Corrective Pattern Analysis:**
   - Analyze the current correction.
   - Clearly state whether it is a **Simple Zigzag** or a **Double Zigzag**.
   - Explain why it is that specific pattern based on the price action.

3. **Fibonacci & Price Levels:**
   - Provide the current Live Price.
   - Give the nearest Fibonacci Retracement levels (0.382, 0.5, 0.618, 0.786).
   - Give Take Profit (TP1, TP2) and Stop Loss (SL) levels.

4. **Trade Recommendation:**
   - Give a clear Buy/Sell/Strong Buy/Strong Sell recommendation.

Do NOT provide generic answers. Your reply must look like an advanced professional chart analysis."""},
                {"role": "user", "content": f"{market_data_text}\nUser Question: {user_message}"}
            ],
            temperature=0.2,
            max_tokens=4096,
        )
        
        bot_reply = response.choices[0].message.content
        footer = f"\n\n---\n🤖 Developed by: Sasith Imarsha | 🎂 Birthday: 2026.08.16"
        
        if len(bot_reply) + len(footer) <= 4096:
            await update.message.reply_text(bot_reply + footer)
        else:
            await update.message.reply_text(bot_reply)

    except Exception as e:
        print(f"Error: {e}")
        await asyncio.sleep(1)
        await handle_message(update, context)

# ==========================================
# 4. Scheduler (පැය 3කට වරක් Top 10)
# ==========================================

async def scheduled_analysis(context: ContextTypes.DEFAULT_TYPE):
    top_10_coins = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT"]
    
    prices = get_live_prices(top_10_coins)
    market_data = ""
    if prices:
        market_data = "\n**📊 3-HOUR REPORT - LIVE PRICES:**\n"
        for symbol, price in prices.items():
            market_data += f"• {symbol}: ${float(price):,.4f}\n"
    else:
        market_data = "\n*(Binance data unavailable.)*\n"

    prompt = f"""{market_data}

Analyze the following Top 10 coins for the next 3 hours: BTC, ETH, SOL, XRP, ADA, DOGE, AVAX, DOT, MATIC, LINK.

For EACH coin, provide:
1. Main Trend (Uptrend/Downtrend) & Elliott Wave Cycle (Wave 1-5).
2. Zigzag/Double Zigzag identification for correction.
3. % Prediction & Recommendation (BUY/SELL).
4. Fibonacci based TP1, TP2, and SL.

100% Sinhala language only.
Provide a complete, structured report."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=4096,
        )
        report = response.choices[0].message.content
        footer = f"\n\n---\n🤖 Developed by: Sasith Imarsha | 🎂 Birthday: 2026.08.16"
        full_message = report + footer
        
        if len(full_message) > 4096:
            await context.bot.send_message(chat_id=context.job.chat_id, text=report)
            await context.bot.send_message(chat_id=context.job.chat_id, text=footer)
        else:
            await context.bot.send_message(chat_id=context.job.chat_id, text=full_message)

    except Exception as e:
        await context.bot.send_message(chat_id=context.job.chat_id, text=f"⚠️ Error generating report: {e}")

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
        job_queue.run_repeating(scheduled_analysis, interval=10800, first=10, chat_id=YOUR_CHAT_ID)
        logging.info("Scheduled analysis set for every 3 hours.")
    else:
        logging.warning("JobQueue not available.")

    print("Bot එක Advanced Elliott Wave + Zigzag Analysis සමඟ පණ ගැහෙමින් පවතී...")
    application.run_polling(drop_pending_updates=True)