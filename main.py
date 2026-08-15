import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# අලුත්ම Google AI පැකේජය import කිරීම
from google import genai

# ==========================================
# 1. API Keys සහ Setup කොටස
# ==========================================

# Render Dashboard එකේ Environment Variables වලට මේ keys දාලා තියෙන්න ඕනේ!
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Logging setup (දෝෂ පෙන්වන්න)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Gemini Client එක පණ ගැන්වීම (අලුත් ක්‍රමය)
client = genai.Client(api_key=GEMINI_API_KEY)

# අලුත්ම නිවැරදි Model එකේ නම (2026 අගෝස්තු වන විට භාවිතා කළ යුතු එක)
# ඔබට අවශ්‍ය නම් 'gemini-2.0-flash-lite' හෝ 'gemini-2.5-pro' ලෙස වෙනස් කරගන්න පුළුවන්
model = genai.GenerativeModel('gemini-2.0-flash-lite')

# ==========================================
# 2. Bot ක්‍රියා කරන Functions
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot එක පණ ගැහුවම පෙන්වන පිළිගැනීමේ පණිවිඩය"""
    await update.message.reply_text("සාදරයෙන් පිළිගනිමු! මම AI බොට් එකක්. මට ඕනෑම දෙයක් අහන්න.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """යවන ලද පණිවිඩ වලට පිළිතුරු දීම"""
    user_message = update.message.text
    
    # User ට "Typing..." කියලා පෙන්නන එක (Optional)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Gemini AI එකට අලුත් ක්‍රමයෙන් Request එක යැවීම
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_message
        )
        
        # උත්තරය ලබාගන්න
        bot_reply = response.text
        
        # Bot උත්තරය User ට යැවීම
        await update.message.reply_text(bot_reply)

    except Exception as e:
        # දෝෂයක් වුනොත් (Ex: API Limit ඉවර වීම හෝ වෙනත් ගැටළු)
        await update.message.reply_text(f"සමාවෙන්න, මට පිළිතුරක් ලබා දීමට නොහැකි විය. දෝෂය: {str(e)}")

# ==========================================
# 3. Bot එක පණ ගැන්වීම (Main Loop)
# ==========================================

if __name__ == "__main__":
    # Telegram Application එක හදාගැනීම
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Commands සහ Messages සඳහා Handlers එකතු කිරීම
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Bot එක Start කිරීම (Polling ක්‍රමය)
    print("Bot එක පණ ගැහෙමින් පවතී...")
    
    # drop_pending_updates=True කියන එක දාන එක වැදගත්. 
    # මෙහෙම කළොත් Server එක Restart වෙන හැම වෙලාවෙම පරණ messages නැවත නැවත පිළිතුරු දෙන්නේ නැහැ.
    application.run_polling(drop_pending_updates=True)