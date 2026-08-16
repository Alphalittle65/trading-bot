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
MODEL_NAME = "gemini-2.5-flash"  # 2026 අගෝස්තු 16 වන විට වැඩ කරන එක

# ==========================================
# 2. Bot ක්‍රියා කරන Functions
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("සාදරයෙන් පිළිගනිමු! මම AI බොට් එකක්.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_message
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text(f"දෝෂය: {str(e)}")

# ==========================================
# 3. 🌟 අලුත්ම කොටස: Webhook Setup කිරීම (මේක තමයි වෙනස)
# ==========================================

async def setup_webhook(application):
    """Bot එක පණ ගැහෙනකොට Webhook එක Set කිරීම"""
    # Render එකෙන් ලැබෙන Port එකත් එක්ක නිවැරදි URL එක හදාගැනීම
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    
    # Free Plan එකේ මේ PORT එක Render එක ඔටෝමැටික්ව දෙනවා
    port = int(os.environ.get("PORT", 10000)) 
    
    if render_url:
        # Webhook එක Set කිරීම (පරණ Polling එක නවත්තලා)
        await application.bot.set_webhook(url=f"{render_url}/webhook")
        logging.info(f"Webhook set to: {render_url}/webhook")
    else:
        logging.warning("RENDER_EXTERNAL_URL not found. Falling back to polling (පරණ ක්‍රමය).")

# ==========================================
# 4. Bot එක පණ ගැන්වීම (Main Loop)
# ==========================================

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Setup webhook before starting
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_webhook(application))

    print("Bot එක Webhook සමඟ පණ ගැහෙමින් පවතී...")
    
    # Webhook ක්‍රමයේදී අපි run_polling පාවිච්චි කරන්නේ නැහැ. 
    # ඒ වෙනුවට Run Webhook එක පණ ගන්වනවා.
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path="/webhook"
    )