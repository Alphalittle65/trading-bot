import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI

# ==========================================
# 1. Setup කොටස
# ==========================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# DeepSeek Client එක පණ ගැන්වීම (OpenAI SDK එකම පාවිච්චි කරයි)
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# ==========================================
# 2. Bot ක්‍රියා කරන Functions
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("සාදරයෙන් පිළිගනිමු! මම DeepSeek AI Trading Assistant.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # DeepSeek API එකට යැවීම
        response = client.chat.completions.create(
            model="deepseek-chat",  # DeepSeek Model එකේ නම
            messages=[
                {"role": "user", "content": user_message}
            ],
            stream=False
        )
        
        # උත්තරය ලබාගන්න
        bot_reply = response.choices[0].message.content
        
        # Bot උත්තරය User ට යැවීම
        await update.message.reply_text(bot_reply)

    except Exception as e:
        # 🛑 කිසිම Error එකක් නිසා Bot එක කඩා වැටෙන්නේ නැහැ!
        print(f"Bot එකට Error එකක් ආවා: {e}")
        
        # තත්පරයක් ඉඳලා ආයෙත් උත්සාහ කරන්න
        await asyncio.sleep(1)
        await handle_message(update, context)

# ==========================================
# 3. Bot එක පණ ගැන්වීම (Main Loop)
# ==========================================

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot එක DeepSeek සමඟ පණ ගැහෙමින් පවතී...")
    
    # Drop pending updates නිසා Conflict එක එන්නේ නැහැ!
    application.run_polling(drop_pending_updates=True)