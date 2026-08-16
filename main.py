import os
import logging
import asyncio
import telegram  # 🌟 මේ පේළිය අලුතින් එකතු කරන්න!
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

# 2026 අගෝස්තු වන විට වැඩ කරන අවසාන Model එක
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

    except telegram.error.RetryAfter as e:
        # 🌟 මේක තමයි Flood Control එක හදන්නා විදිය
        # තත්පර කිහිපයක් ඉඳලා ආයෙත් උත්සාහ කරනවා
        await asyncio.sleep(e.retry_after)
        # නැවත උත්සාහ කිරීමට මේ ෆන්ක්ෂන් එකම call කරන්න
        await handle_message(update, context)

    except Exception as e:
        await update.message.reply_text(f"දෝෂය: {str(e)}")

# ==========================================
# 3. Webhook Setup කිරීම (මේක නිසා Sleep ගැටළුව නැහැ)
# ==========================================

async def setup_webhook(application):
    render_url = os.getenv("RENDER_EXTERNAL_URL")
    port = int(os.environ.get("PORT", 10000))
    
    if render_url:
        await application.bot.set_webhook(url=f"{render_url}/webhook")
        logging.info(f"Webhook set to: {render_url}/webhook")
    else:
        logging.warning("RENDER_EXTERNAL_URL not found. Falling back to polling.")

# ==========================================
# 4. Bot එක පණ ගැන්වීම (Main Loop)
# ==========================================

if __name__ == "__main__":
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Webhook Setup
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_webhook(application))

    print("Bot එක Webhook සමඟ පණ ගැහෙමින් පවතී...")
    
    # Run Webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        url_path="/webhook"
    )