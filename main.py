import os
import logging
import asyncio
import base64
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
from groq import Groq

# ==========================================
# 1. Setup කොටස
# ==========================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ඔබේ Chat ID එක මෙතනට අලවන්න (උදා: 123456789)
YOUR_CHAT_ID = 123456789  # <--- මෙතනට ඔබේ Chat ID අංකය අලවන්න!

BINANCE_API_URL = "https://api.binance.com/api/v3/ticker/price"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Groq Client Setup
client = Groq(api_key=GROQ_API_KEY)

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
        f"🤖 **Ultimate Trading Bot with Groq Vision**\n"
        f"📊 Binance Live Price ලබා ගත හැක.\n"
        f"🖼️ TradingView Chart එකක Image එකක් යවා විශ්ලේෂණය කරගන්න.\n"
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
        # 🖼️ Image/Chart Analysis Check
        if update.message.photo:
            # පින්තූරය ගන්න
            photo_file = await update.message.photo[-1].get_file()
            image_bytes = await photo_file.download_as_bytearray()
            
            # පින්තූරය Base64 බවට හරවන්න (Groq සඳහා)
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Groq Vision එකට යැවීම
            response = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",  # Groq හි Vision Model එක
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this Trading Chart. Provide Fibonacci levels, Support, Resistance, and Elliott Wave status."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    }
                ],
                max_tokens=1024
            )
            
            await update.message.reply_text(response.choices[0].message.content)
            return

        # 💬 Text Message Check
        if "top" in user_message.lower() or "gain" in user_message.lower() or "හොඳම" in user_message.lower():
            await update.message.reply_text("📊 Binance මගින් Top 5 Gainers සොයමින්...")
            await update.message.reply_text("🔍 මේ සඳහා අමතර කේතයක් අවශ්‍ය වේ.")
            return

        if "price" in user_message.lower():
            symbol = user_message.split()[0].upper().replace("USDT", "") + "USDT"
            prices = get_live_prices([symbol])
            if symbol in prices:
                await update.message.reply_text(f"📊 **{symbol}** Live Price: ${float(prices[symbol]):,.4f}")
            else:
                await update.message.reply_text(f"⚠️ {symbol} සඳහා මිල සොයාගත නොහැක.")
            return

        # සාමාන්‍ය ප්‍රශ්න සඳහා Text AI පිළිතුරු (Groq Text)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"100% Sinhala language only. {user_message}"}],
            temperature=0.7,
            max_tokens=1024
        )
        await update.message.reply_text(response.choices[0].message.content)

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

    print("Bot එක Groq Vision + Live Price සමඟ පණ ගැහෙමින් පවතී...")
    application.run_polling(drop_pending_updates=True)