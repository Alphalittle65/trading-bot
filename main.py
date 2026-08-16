import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# ==========================================
# 1. Setup කොටස
# ==========================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# 2. Bot ක්‍රියා කරන Functions
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("සාදරයෙන් පිළිගනිමු! මම Advanced Trading Analyst Bot. මම සෑම පැය 3කට වරක්ම වෙළඳපොල විශ්ලේෂණය කරලා මෙතනටම යවනවා.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": """You are the world's best Crypto Market Analyst. 
You MUST reply in Sinhala language ONLY.
Analyze the coins mentioned by the user and provide:
1. Market Trend (Uptrend/Downtrend) for the next 3 hours.
2. Percentage Prediction (%).
3. Trade Recommendation (BUY, STRONG BUY, SELL, STRONG SELL).
4. Take Profit (TP) levels (2 levels).
5. Stop Loss (SL) level (1 level).
6. Liquidity Zone.
7. Elliott Wave Analysis."""},
                {"role": "user", "content": user_message}
            ],
            temperature=0.2,
            max_tokens=2048,
        )
        await update.message.reply_text(response.choices[0].message.content)

    except Exception as e:
        print(f"Error: {e}")
        await asyncio.sleep(1)
        await handle_message(update, context)

# ==========================================
# 3. ⏰ සෑම පැය 3කට වරක් විශ්ලේෂණය කරන කොටස (Scheduler)
# ==========================================

async def scheduled_analysis(context: ContextTypes.DEFAULT_TYPE):
    # මෙතනට ඔබට විශ්ලේෂණය කරන්න ඕන කාසි 10ක නම් දාන්න (උදා: BTC, ETH, SOL, XRP, ADA, DOGE, AVAX, DOT, MATIC, LINK)
    coins = "BTC, ETH, SOL, XRP, ADA, DOGE, AVAX, DOT, MATIC, LINK"
    
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=f"🕒 **පැය 3ක විශ්ලේෂණය (Top 10 Coins):**\n\nසියලුම කාසි සඳහා විශ්ලේෂණය ආරම්භ වෙමින් පවතී... කරුණාකර තත්පර කිහිපයක් ඉන්න."
    )

    try:
        # Groq එකට එකපාරටම කාසි 10ම යවනවා
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": """You are the world's best Crypto Market Analyst. 
You MUST reply in Sinhala language.
Analyze the following 10 coins: BTC, ETH, SOL, XRP, ADA, DOGE, AVAX, DOT, MATIC, LINK.
For EACH coin, provide:
1. Trend for next 3 hours (Uptrend/Downtrend)
2. % Prediction
3. Trade (BUY/SELL/STRONG BUY/STRONG SELL)
4. TP1 & TP2 Levels
5. SL Level
6. Liquidity Zone
7. Elliott Wave Status

Give me a clear, bulleted report."""},
                {"role": "user", "content": "Analyze these 10 coins for the next 3 hours with full technical details."}
            ],
            temperature=0.2,
            max_tokens=4096,
        )
        
        report = response.choices[0].message.content
        # රිපෝට් එක යවන්න (එයා ලොකු නිසා කෑලි කිහිපයකට කඩලා යවන්න සිදු වෙයි)
        await context.bot.send_message(chat_id=context.job.chat_id, text=report)

    except Exception as e:
        await context.bot.send_message(chat_id=context.job.chat_id, text=f"විශ්ලේෂණය අසාර්ථක විය. Error: {e}")

# ==========================================
# 4. Bot එක පණ ගැන්වීම (Main Loop)
# ==========================================

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 🌟 Scheduler එක පණ ගැන්වීම (පැය 3කට වරක්)
    # මෙතන chat_id එකට ඔබේ ඇත්ත Telegram ID එක දාන්න! 
    # ඔබට ඔබේ ID එක දැනගන්න @userinfobot වගේ Bot එකකට Message එකක් යවලා බලන්න පුළුවන්.
    job_queue = application.job_queue
    job_queue.run_repeating(scheduled_analysis, interval=10800, first=10, chat_id=YOUR_TELEGRAM_ID)

    print("Bot එක Advanced Scheduler සමඟ පණ ගැහෙමින් පවතී...")
    application.run_polling(drop_pending_updates=True)