import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq
import requests

# ==========================================
# 1. Setup කොටස (API Keys සහ Settings)
# ==========================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ඔබේ Chat ID එක මෙතනට අලවන්න (උදා: 123456789)
YOUR_CHAT_ID = 123456789  # <--- මෙතනට ඔබේ ඇත්ත ID අංකය අලවන්න!

# Binance API Endpoint
BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# 2. Binance Data ලබා ගැනීමේ ක්‍රමය
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
# 3. Bot ක්‍රියා කරන Functions
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
    """පරිශීලකයාට තමන්ගේ Chat ID එක පෙන්වීම"""
    await update.message.reply_text(f"ඔබේ Telegram Chat ID එක: `{update.effective_chat.id}`")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # පරිශීලකයා කාසි ගැන අසනවාදැයි පරීක්ෂා කිරීම
        coin_keywords = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT", "MATIC", "LINK"]
        found_coins = []
        for coin in coin_keywords:
            if coin in user_message.upper():
                found_coins.append(coin)
        
        market_data_text = ""
        if found_coins:
            prices = get_live_prices(found_coins)
            if prices:
                market_data_text = "\n**📈 සජීවී වෙළඳපොල දත්ත (Binance):**\n"
                for symbol, price in prices.items():
                    market_data_text += f"• {symbol}: ${float(price):,.4f}\n"
                market_data_text += "\n"
            else:
                market_data_text = "\n*(Binance දත්ත ලබා ගැනීමට නොහැකි විය.)*\n\n"

        # Groq AI එකට යැවීම
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"""You are the world's best Crypto Trading Analyst.
ABSOLUTE RULE: You MUST reply ONLY in Sinhala language.
ALWAYS be precise and professional.
Analyze the user's query. Use the provided live market data if available.
Provide:
1. Trend for next 3 hours (Uptrend/Downtrend/Sideways)
2. % Prediction
3. Recommendation (BUY/SELL/STRONG BUY/STRONG SELL)
4. TP1 & TP2
5. SL
6. Liquidity Zone
7. Elliott Wave Status."""},
                {"role": "user", "content": f"{market_data_text}\nUser's Question: {user_message}"}
            ],
            temperature=0.3,
            max_tokens=2048,
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
# 4. ⏰ පැය 3ක Scheduler (Top 10 Coins සඳහා)
# ==========================================

async def scheduled_analysis(context: ContextTypes.DEFAULT_TYPE):
    top_10_coins = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT"]
    
    prices = get_live_prices(top_10_coins)
    market_data = ""
    if prices:
        market_data = "\n**📊 පැය 3ක වාර්තාව සඳහා සජීවී දත්ත:**\n"
        for symbol, price in prices.items():
            market_data += f"• {symbol}: ${float(price):,.4f}\n"
    else:
        market_data = "\n*(Binance දත්ත ලබා ගැනීමට නොහැකි විය.)*\n"

    prompt = f"""{market_data}

පහත සඳහන් Top 10 කාසි සඳහා පැය 3ක විශ්ලේෂණයක් සපයන්න: BTC, ETH, SOL, XRP, ADA, DOGE, AVAX, DOT, MATIC, LINK.

එක් එක් කාසිය සඳහා:
1. Trend (Uptrend/Downtrend)
2. % Change Prediction
3. Recommendation (BUY/SELL)
4. TP1 & TP2
5. SL
6. Liquidity Zone
7. Elliott Wave Cycle

100% සිංහල භාෂාවෙන් පමණක් උත්තර සපයන්න."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
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
        await context.bot.send_message(chat_id=context.job.chat_id, text=f"⚠️ වාර්තාව සැකසීමේදී දෝෂයක්: {e}")

# ==========================================
# 5. Bot එක පණ ගැන්වීම (Main Loop)
# ==========================================

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", my_id))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 🌟 Scheduler එක පණ ගැන්වීම (පැය 3කට වරක්)
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(scheduled_analysis, interval=10800, first=10, chat_id=YOUR_CHAT_ID)
        logging.info("Scheduled analysis set for every 3 hours.")
    else:
        logging.warning("JobQueue not available.")

    print("Bot එක Groq + Binance සමඟ පණ ගැහෙමින් පවතී...")
    application.run_polling(drop_pending_updates=True)