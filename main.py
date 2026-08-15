import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ==========================================
# 1. අලුත්ම Google AI පැකේජය import කිරීම (google-genai)
# ==========================================
from google import genai

# ==========================================
# 2. API Keys සහ Setup කොටස
# ==========================================

# Render Dashboard එකේ Environment Variables වලට මේ keys දාලා තියෙන්න ඕනේ!
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Logging setup (දෝෂ පෙන්වන්න)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# අලුත්ම විදියට Gemini Client එක පණ ගැන්වීම
client = genai.Client(api_key=GEMINI_API_KEY)

# දැනට වඩාත්ම නිවැරදිව වැඩ කරන Model එකේ නම
MODEL_NAME = "gemini-1.5-flash"  
# (සටහන: 2026 අගෝස්තු 12න් පසු මේක 'gemini-2.0-flash-lite' වලට මාරු කරන්න)

# ==========================================
# 3. Bot ක්‍රියා කරන Functions
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot එක පණ ගැහුවම පෙන්වන පිළිගැනීමේ පණිවිඩය"""
    await update.message.reply_text("සාදරයෙන් පිළිගනිමු! මම AI බොට් එකක්. මට ඕනෑම දෙයක් අහන්න.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """යවන ලද පණිවිඩ වලට පිළිතුරු දීම"""
    user_message = update.message.text
    
    # User ට "Typing..." කියලා පෙන්නන එක (ඔප්ෂන්)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # ==========================================
        # 🌟 අලුත්ම ක්‍රමය: Gemini AI එකට Request එක යැවීම
        # ==========================================
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_message
        )
        
        # උත්තරය ලබාගන්න
        bot_reply = response.text
        
        # Bot උත්තරය User ට යැවීම
        await update.message.reply_text(bot_reply)

    except Exception as e:
        # දෝෂයක් වුනොත් (Ex: API Limit ඉවර වීම)
        await update.message.reply_text(f"සමාවෙන්න, මට පිළිතුරක් ලබා දීමට නොහැකි විය. දෝෂය: {str(e)}")

# ==========================================
# 4. Bot එක පණ ගැන්වීම (Main Loop)
# ==========================================

if __name__ == "__main__":
    # Telegram Application එක හදාගැනීම
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Commands සහ Messages සඳහා Handlers එකතු කිරීම
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ==========================================
    # 🌟 අතිශයින් වැදගත්: පරණ සම්බන්ධතා කපා හැරීම
    # ==========================================
    # මේ පේළිය නිසා Bot එක Start වෙන හැම වෙලාවෙම Conflict එක වැළකෙනවා
    asyncio.run(application.bot.delete_webhook(drop_pending_updates=True))
    
    print("Bot එක පණ ගැහෙමින් පවතී...")
    
    # Bot එක Start කිරීම
    application.run_polling()