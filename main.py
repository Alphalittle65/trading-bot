import os
import asyncio
from aiohttp import web
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
from google.genai import types

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

ai_client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
You are an intelligent, highly analytical, and helpful AI assistant powered by Gemini. 
When responding to any query:
1. Think deeply and analyze step-by-step before answering.
2. Provide clear, direct, and accurate responses to ANY topic.
3. Match the user's language (Sinhala or English).
"""

async def handle_http(request):
    return web.Response(text="Bot is active!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "හලෝ! 👋 මම Gemini AI තාක්ෂණයෙන් බලගන්වපු ඔයාගේ Smart Assistant. මගෙන් ඕනෑම දෙයක් අහන්න!"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
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

async def main():
    # Setup Telegram Bot
    telegram_app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Setup Async HTTP Server for Render Port Binding
    web_app = web.Application()
    web_app.router.add_get('/', handle_http)
    web_app.router.add_head('/', handle_http)
    
    port = int(os.environ.get("PORT", 8080))
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")

    # Start Telegram Polling safely within the same asyncio loop
    async with telegram_app:
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        print("Bot Polling started successfully!")
        
        # Keep running continuously
        await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())