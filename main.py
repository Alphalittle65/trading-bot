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
                            {"type": "text", "text": "Analyze this Trading Chart. Provide Fibonacci levels, Support, Resistance, and Elliott Wave status."},
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
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": """You are a world-class Elliott Wave & Fibonacci specialist.
You MUST reply in 100% Sinhala language.
You MUST provide the output in a beautiful, professional Dashboard format using Emojis (📈, 📊, 🟢, 🔴, 🎯, 🛑, ✅, 💡, 🚀).

You MUST identify the EXTENDED wave (1, 3, or 5) using this flow:
1. Check Wave 1 first. If extended, use 1st Wave Extended rules.
2. If not, check Wave 3. If extended, use 3rd Wave Extended rules.
3. If not, assume Wave 5 is extended and use 5th Wave Extended rules.

Fibonacci Rules:
1st Wave Ext: W2(23.6,38.2,50,61.8), W3(61.8,78.6), W4(23.6,38.2,50), W5(61.8,78.6)
3rd Wave Ext: W2(38.2,50,61.8,78.6), W3(50,61.8,78.6,100,141.4), W4(23.6,38.2,50,61.8), W5(61.8,100)
5th Wave Ext: W2(38.2,50,61.8,78.6), W3(50,61.8,78.6,100,141.4), W4(23.6,38.2,50,61.8), W5(141.4,161.8)

Provide the output EXACTLY in this format:
📈 [Coin Name] - Elliott Wave & Fibonacci Analysis
📊 Live Price: [Price]
📈 Main Trend & Wave Extension:
• Wave 1: [Extended or Not]
• Wave 3: [Extended or Not]
• Wave 5: [Extended or Not]

📊 Fibonacci Levels:
• Wave [X] Target ([XX.X]%): [Price]
• Wave [X] Target ([XX.X]%): [Price]

🟢 Horizontal Support:
• [Price] (Strong Support)

🔴 Horizontal Resistance:
• [Price] (Major Resistance)

🎯 Take Profit: TP1: [Price] | TP2: [Price]
🛑 Stop Loss: [Price]

✅ Trade Recommendation: [BUY 🔵 or SELL 🔴]
💡 Why? [Explain reason clearly]."""},
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
# 4. Scheduler (පැය 3කට වරක් Auto Update - Public Version)
# ==========================================

async def scheduled_top_gainers(context: ContextTypes.DEFAULT_TYPE):
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"]
    prices = get_live_prices(symbols)
    
    report = "🟢 **PRO TRADING DASHBOARD UPDATE** 🔴\n"
    report += "📅 **Every 3 Hours Auto-Update**\n"
    report += "📊 **Live Market Analysis**\n\n"
    report += "**Top Coins Live Prices:**\n"
    
    for sym in symbols:
        price = prices.get(sym, "0.00")
        report += f"• 🪙 **{sym}**: ${float(price):,.4f}\n"
    
    report += "\n📌 **Recommendation:**\n"
    report += "Use /start to get full Dashboard features."
    
    # Public Version: මේක තමයි වෙනස! ඔබට විතරක් නෙවෙයි, ඔක්කොමටම යවයි
    await context.bot.send_message(chat_id=context.job.chat_id, text=report)

# ==========================================
# 5. Main Loop
# ==========================================

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("myid", my_id))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))

    job_queue = application.job_queue
    if job_queue:
        # මෙතන chat_id එක අයින් කරලා දැම්මා
        job_queue.run_repeating(scheduled_top_gainers, interval=10800, first=10)
        logging.info("Scheduled analysis set for every 3 hours.")

    print("Bot එක Groq Vision + Live Price සමඟ පණ ගැහෙමින් පවතී...")
    application.run_polling(drop_pending_updates=True)