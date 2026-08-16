import os
import logging
import asyncio
import base64
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import google.generativeai as genai

# ==========================================
# 1. Setup කොටස
# ==========================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ඔබේ Chat ID එක මෙතනට අලවන්න (උදා: 123456789)
YOUR_CHAT_ID = 123456789  # <--- මෙතනට ඔබේ Chat ID අංකය අලවන්න!

BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Gemini Vision AI Setup (1.5 Pro මාදිලිය Image බැලීමට සුදුසුයි)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# ==========================================
# 2. Binance Data Function
# ==========================================

def get_live_prices(symbols):
    try:
        response = requests.get(BINANCE_API_URL)
        if response.status_code == 200:
            all_prices = response.json()
            filtered = {item['symbol']: item['price'] for item in all_prices if item['symbol'] in symbols}
            return filtered
        return {}
    except Exception as e:
        logging.error(f"Binance Error: {e}")
        return {}

# ==========================================
# 3. Bot Functions
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        f"🟢 **සාදරයෙන් පිළිගනිමු!** 🟢\n\n"
        f"🤖 **Ultimate Trading Bot with Vision AI**\n"
        f"📊 Binance Live Price ලබා ගත හැක.\n"
        f"🖼️ TradingView Chart එකක Image එකක් යවා Fibonacci / Wave විශ්ලේෂණය කරගන්න.\n"
        f"💬 කාසියක නම අමතා විශ්ලේෂණය ලබා ගන්න.\n\n"
        f"**අලුත් Command:** ඔබේ Chat ID එක දැනගන්න `/myid` ටයිප් කරන්න."
    )
    await update.message.reply_text(welcome_msg)

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"ඔබේ Telegram Chat ID එක: `{update.effective_chat.id}`")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # 🖼️ Image/Chart Analysis Check (පින්තූරයක් එවලා තියෙනවා නම්)
        if update.message.photo:
            # අන්තිමට එවපු පින්තූරය ගන්න
            photo_file = await update.message.photo[-1].get_file()
            # පින්තූරය දත්ත (bytes) ලෙස ගන්න
            image_bytes = await photo_file.download_as_bytearray()
            
            # Gemini Vision එකට පින්තූරය යවන්න
            response = model.generate_content([
                "මෙම Trading Chart එක විශ්ලේෂණය කරන්න. Fibonacci Levels, Support, Resistance, සහ Elliott Wave තත්වය පෙන්වන්න. 100% සිංහලෙන් උත්තර දෙන්න.",
                {"mime_type": "image/jpeg", "data": image_bytes}
            ])
            
            await update.message.reply_text(response.text)
            return

        # 💬 Text Message Check
        # Top Gainers Check
        if "top" in user_message.lower() or "gain" in user_message.lower() or "හොඳම" in user_message.lower():
            await update.message.reply_text("📊 Binance මගින් Top 5 Gainers සොයමින්...")
            
            # ඔබට අවශ්‍ය නම් මෙතනට Top Gainers Logic එක එකතු කරගන්න.
            # සරලව පිළිතුරු දීමට:
            await update.message.reply_text("🔍 මේ සඳහා අමතර කේතයක් අවශ්‍ය වේ.")
            return

        # Normal Coin Price & Analysis
        if "price" in user_message.lower():
            symbol = user_message.split()[0].upper().replace("USDT", "") + "USDT"
            prices = get_live_prices([symbol])
            if symbol in prices:
                await update.message.reply_text(f"📊 **{symbol}** Live Price: ${float(prices[symbol]):,.4f}")
            else:
                await update.message.reply_text(f"⚠️ {symbol} සඳහා මිල සොයාගත නොහැක.")
            return

        # සාමාන්‍ය ප්‍රශ්න සඳහා Text AI පිළිතුරු
        response = model.generate_content(f"100% සිංහලෙන් පමණක් පිළිතුරු දෙන්න. {user_message}")
        await update.message.reply_text(response.text)

    except Exception as e:
        print(f"Error: {e}")
        await asyncio.sleep(1)
        await handle_message(update, context)

# ==========================================
# 4. Main Loop
# ==========================================

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", my_id))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))

    print("Bot එක Gemini Vision + Live Price සමඟ පණ ගැහෙමින් පවතී...")
    application.run_polling(drop_pending_updates=True)