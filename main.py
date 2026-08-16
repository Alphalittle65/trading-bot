import os
import logging
import asyncio
import telegram
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

# 2026 අගෝස්තු වන විට වැඩ කරන අවසාන Free Model එක
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
        # 🛑 ඕනෑම Error එකක් ආවත් Bot එක කඩා වැටෙන්නේ නැහැ!
        print(f"Bot එකට Error එකක් ආවා: {e}")
        
        # තත්පරයක් ඉඳලා ආයෙත් උත්සාහ කිරීමට (Recursion)
        await asyncio.sleep(1)
        await handle_message(update, context)

# ==========================================
# 3. Webhook Setup කිරීම
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

    # 🌟 Webhook Setup සඳහා Event Loop එක හදාගැනීම
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 🌟 අතිශයින් වැදගත්: පරණ Webhook / Polling සම්බන්ධතා බලෙන් මකා දැමීම
    # මේක නිසා කිසිම Conflict එකක් එන්නේ නැහැ!
    loop.run_until_complete(application.bot.delete_webhook(drop_pending_updates=True))

    # 🌟 අලුත් Webhook එක Set කිරීම
    loop.run_until_complete(setup_webhook(application))

    print("Bot එක Webhook සමඟ පණ ගැහෙමින් පවතී...")
    
    # 🌟 Run Webhook (max_connections=5 මගින් Flood Control එක අඩු කරයි)
        # 🌟 අලුත් කොටස: Bot එක කඩා වැටුණොත් තත්පරයක් ඉඳලා ආයෙත් උත්සාහ කරන්න
    while True:
        try:
            application.run_webhook(
                listen="0.0.0.0",
                port=int(os.environ.get("PORT", 10000)),
                url_path="/webhook",
                max_connections=5
            )
            break  # සාර්ථක වුනොත් loop එකෙන් එලියට යන්න
        except Exception as e:
            print(f"Webhook එක කඩා වැටුණා. තත්පරයකින් නැවත උත්සාහ කරයි. Error: {e}")
            asyncio.sleep(1)