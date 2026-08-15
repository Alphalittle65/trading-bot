import os
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai  # මෙය එකතු කරන්න

# Render Port Binding
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Trading Bot is Active")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Gemini Client නිවැරදිව configure කරන්න
genai.configure(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
You are an intelligent, highly analytical, and helpful AI assistant powered by Gemini. 
When responding to any query:
1. Think deeply and analyze step-by-step before answering.
2. Provide clear, direct, and accurate responses to ANY topic.
3. Match the user's language (Sinhala or English).
"""

# Model එක system_instruction සමඟ initialize කරන්න
model = genai.GenerativeModel(
    model_name='gemini-2.0-flash',
    system_instruction=SYSTEM_INSTRUCTION
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "හලෝ! 👋 මම Gemini AI තාක්ෂණයෙන් බලගන්වපු ඔයාගේ Smart Assistant. මගෙන් ඕනෑම දෙයක් අහන්න!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # නිවැරදි generate_content ක්‍රමය
        response = model.generate_content(
            user_text,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
            )
        )
        
        answer = response.text
        if len(answer) > 4000:
            for i in range(0, len(answer), 4000):
                await update.message.reply_text(answer[i:i+4000])
        else:
            await update.message.reply_text(answer)

    except Exception as e:
        print(f"Gemini Error: {e}")
        await update.message.reply_text(f"⚠️ Error: {str(e)}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Starting bot...")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        poll_interval=1.0,
        timeout=30
    )

if __name__ == '__main__':
    main()