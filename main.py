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
        f"💬 කාසියක නම අමතා හරියටම ඔබේ Fibonacci Rules වලට අනුව විශ්ලේෂණය ලබා ගන්න.\n\n"
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
            photo_file = await update.message.photo[-1].get_file()
            image_bytes = await photo_file.download_as_bytearray()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            response = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Analyze this Trading Chart. Provide Fibonacci levels, Support, Resistance, and Elliott Wave status based on user's custom Fibonacci rules."},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                        ]
                    }
                ],
                max_tokens=1024
            )
            await update.message.reply_text(response.choices[0].message.content)
            return

        # 💬 Live Price Check
        if "price" in user_message.lower():
            symbol = user_message.split()[0].upper().replace("USDT", "") + "USDT"
            prices = get_live_prices([symbol])
            if symbol in prices:
                await update.message.reply_text(f"📊 **{symbol}** Live Price: ${float(prices[symbol]):,.4f}")
            else:
                await update.message.reply_text(f"⚠️ {symbol} සඳහා මිල සොයාගත නොහැක.")
            return

        # 📈 Text Analysis with Dashboard Output
        # මෙතන තමයි ඔබේ Fibonacci Rules භාවිතා කරලා උත්තර හදන්නේ
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": """You are a world-class Elliott Wave & Fibonacci specialist.
You MUST reply in 100% Sinhala language.
You MUST provide the output in a beautiful, professional Dashboard format using Emojis (📈, 📊, 🟢, 🔴, 🎯, 🛑, ✅, 💡, 🚀).

ABSOLUTE RULE: You MUST NOT include any history, fundamentals, or descriptions of the coin. ONLY provide pure technical live analysis.
You MUST use the live market price provided in the user's prompt to calculate ALL levels.

You MUST identify the EXTENDED wave (1, 3, or 5) using this flow:
1. Check Wave 1 first. If extended, use 1st Wave Extended rules.
2. If not, check Wave 3. If extended, use 3rd Wave Extended rules.
3. If not, assume Wave 5 is extended and use 5th Wave Extended rules.

Fibonacci Rules (User's Custom Rules):
1st Wave Ext: W2(23.6,38.2,50,61.8), W3(61.8,78.6), W4(23.6,38.2,50), W5(61.8,78.6)
3rd Wave Ext: W2(38.2,50,61.8,78.6), W3(50,61.8,78.6,100,141.4), W4(23.6,38.2,50,61.8), W5(61.8,100)
5th Wave Ext: W2(38.2,50,61.8,78.6), W3(50,61.8,78.6,100,141.4), W4(23.6,38.2,50,61.8), W5(141.4,161.8)

Provide the output EXACTLY in this format:
📈 [Coin Name] - Elliott Wave & Fibonacci Analysis
📊 Live Price: [Live Market Price]
📈 Main Trend & Wave Extension:
• Wave 1: [Extended or Not Extended]
• Wave 3: [Extended or Not Extended]
• Wave 5: [Extended or Not Extended]

📊 Fibonacci Levels (Based on your custom rules):
• Wave [X] Target ([XX.X]%): [Calculated Price]
• Wave [X] Target ([XX.X]%): [Calculated Price]

🟢 Horizontal Support:
• [Calculated Price] (Strong Support)

🔴 Horizontal Resistance:
• [Calculated Price] (Major Resistance)

🎯 Take Profit: TP1: [Calculated Price] | TP2: [Calculated Price]
🛑 Stop Loss: [Calculated Price]

✅ Trade Recommendation: BUY 🔵 or SELL 🔴
💡 Why? [Brief technical reason based on the wave and fib levels]."""},
                {"role": "user", "content": f"{user_message}"}
            ],
            temperature=0.3,
            max_tokens=2048
        )
        
        bot_reply = response.choices[0].message.content
        await update.message.reply_text(bot_reply)

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

    print("Bot එක Groq Vision + Custom Fibonacci Rules සමඟ පණ ගැහෙමින් පවතී...")
    application.run_polling(drop_pending_updates=True)