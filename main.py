import os
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

# Render Port Binding Fix
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active")

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

ai_client = genai.Client(api_key=GEMINI_API_KEY)

# AI එක වැඩ කල යුතු ආකාරය (System Instruction)
SYSTEM_INSTRUCTION = """
You are an intelligent, highly analytical, and helpful AI assistant powered by Gemini. 
When responding to any query:
1. Think deeply, step-by-step, analyzing all sides of the user's prompt before providing an answer.
2. Provide clear, direct, accurate, and comprehensive responses to ANY topic (Trading, Tech, General Knowledge, Logic, Business, etc.).
3. Match the user's language (if asked in Sinhala, reply in natural Sinhala, if asked in English, reply in English).
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "හලෝ! 👋 මම Gemini AI තාක්ෂණයෙන් බලගන්වපු ඔයාගේ Smart Assistant. ඕනෑම විෂයයක් හෝ ප්‍රශ්නයක් ගැන මගෙන් අහන්න!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        # Gemini 2.5 Flash model එක deep thinking instruction එක සමග Call කිරීම
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
            )
        )
        
        # Telegram Message එකක් දීර්ඝ වැඩි නම් කඩා යැවීමට
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
    print("Bot is polling...")
    app.run_polling()

if __name__ == '__main__':
    main()