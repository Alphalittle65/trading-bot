import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# ==========================================
# 1. API Keys සහ Setup කොටස
# ==========================================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

client = genai.Client(api_key=GEMINI_API_KEY)

# 2026 අගෝස්තු වන විට නිවැරදිව වැඩ කරන Free Model එක
MODEL_NAME = "gemini-2.5-flash" 

# ==========================================
# 2. Bot ක්‍රියා කරන Functions
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("සාදරයෙන් පිළිගනිමු! මම ඔබේ Trading AI Assistant.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Gemini API එකට යැවීම
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_message
        )
        await update.message.reply_text(response.text)

    except Exception as e:
        # 🛑 කිසිම Error එකක් නිසා Bot එක කඩා වැටෙන්නේ නැහැ!
        print(f"Bot එකට Error එකක් ආවා: {e}")
        
        # තත්පරයක් ඉඳලා ආයෙත් උත්සාහ කරන්න (Recursion)
        await asyncio.sleep(1)
        await handle_message(update, context)

# ==========================================
# 3. Bot එක පණ ගැන්වීම (Main Loop)
# ==========================================

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot එක පණ ගැහෙමින් පවතී... (Polling ක්‍රමය)")
    
    # 🌟 Render Free Plan එකේ 'No open ports' ගැටළුව විසඳීමට මේ පේළිය
    port = int(os.environ.get("PORT", 10000))
    
    # 🌟 Drop pending updates නිසා Conflict එක එන්නේ නැහැ!
    application.run_polling(drop_pending_updates=True)