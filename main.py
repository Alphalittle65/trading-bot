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

# Groq Client එක පණ ගැන්වීම
client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# 2. Bot ක්‍රියා කරන Functions
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("සාදරයෙන් පිළිගනිමු! මම Groq AI Trading Assistant.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Groq API එකට ඉංග්‍රීසියෙන් යැවීම
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # වේගවත්ම Free Model එක
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Always reply in Sinhala language."}, # සිංහලෙන් උත්තර දෙන්න කියන උපදෙස
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=1024,
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

    print("Bot එක Groq සමඟ පණ ගැහෙමින් පවතී...")
    
    # Drop pending updates නිසා Conflict එක එන්නේ නැහැ!
    application.run_polling(drop_pending_updates=True)