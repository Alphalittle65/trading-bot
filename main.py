import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# Environment Variables මගින් Keys ලබා ගැනීම
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Gemini Client එක Initialize කිරීම (නව SDK එකට අනුව)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(
        f"හලෝ {user_first_name}! 👋\nමම ඔයාගේ AI Trading Assistant Bot. මගෙන් ඕනෑම ප්‍රශ්නයක් අහන්න!"
    )

# Messages සදහා Gemini Response ලබාදෙන Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # Telegram එකේ "Typing..." කියා පෙන්වීමට
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Gemini API එක හරහා පිළිතුර ලබා ගැනීම (gemini-2.5-flash භාවිතයෙන්)
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
        )
        
        reply_text = response.text
        await update.message.reply_text(reply_text)
        
    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("කණගාටුයි, පිළිතුර ලබාගැනීමේදී දෝෂයක් සිදු වුණා. කරුණාකර පසුව නැවත උත්සාහ කරන්න.")

# Main Function එක
def main():
    if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
        print("Error: API Keys ලබාදී නැත! Render Environment Variables පරීක්ෂා කරන්න.")
        return

    # Telegram Application එක Build කිරීම
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers එකතු කිරීම
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    # Polling ආරම්භ කිරීම
    app.run_polling()

if __name__ == '__main__':
    main()