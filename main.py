import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# API Keys
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = "AIzaSy..."  # ඔයාගේ සම්පූර්ණ API Key එක මෙතනට Paste කරන්න

ai_client = genai.Client(api_key=GEMINI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(
        f"හලෝ {user_first_name}! 👋\nමම ඔයාගේ AI Trading Assistant Bot. මගෙන් ඕනෑම ප්‍රශ්නයක් අහන්න!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("කණගාටුයි, පිළිතුර ලබාගැනීමේදී දෝෂයක් සිදු වුණා.")

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is missing in Render Environment Variables!")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()