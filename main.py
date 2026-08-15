import os
import time
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from scanner.multi_coin import fetch_all_market_data
from analysis.fibonacci import calculate_fibonacci_levels, format_fib_for_ai
from analysis.elliott_wave import detect_swing_points, format_elliott_context

# Environment variables load කිරීම
load_dotenv()

BRAIN_FILE = Path("brain/master_brain.txt")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = "1419561512"  # ඔයාගේ Telegram Chat ID එක

def load_brain():
    if not BRAIN_FILE.exists():
        return "You are an expert crypto trading AI. Provide concise Technical Analysis in JSON."
    return BRAIN_FILE.read_text(encoding="utf-8")

def connect_ai():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from .env file!")
    genai.configure(
        api_key=api_key,
        client_options={"api_endpoint": "generativelanguage.googleapis.com/v1"}
    )

def analyze_single_coin(symbol, mtf_data, brain_instructions):
    fib_levels = calculate_fibonacci_levels(mtf_data["4h"])
    fib_text = format_fib_for_ai(fib_levels)
    
    swings = detect_swing_points(mtf_data["1h"])
    elliott_text = format_elliott_context(swings)

    current_close = mtf_data["15m"]["close"].iloc[-1]

    prompt = f"""
{brain_instructions}

=== COIN: {symbol} (Current Price: ${current_close:.2f}) ===
FIBONACCI: {fib_text}
ELLIOTT WAVE: {elliott_text}

Analyze this pair strictly following system instructions. Respond ONLY in valid JSON format like this:
{{
    "symbol": "{symbol}",
    "decision": "LONG",
    "score": 85,
    "entry": {current_close:.2f},
    "sl": {current_close * 0.99:.2f},
    "tp": {current_close * 1.03:.2f},
    "reason": "Short summary of technical setup"
}}
"""
    target_models = ["gemini-2.5-flash", "gemini-2.0-flash"]

    for model_name in target_models:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={"response_mime_type": "application/json"}
            )
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            if raw_text.startswith("```json"): raw_text = raw_text[7:]
            if raw_text.startswith("```"): raw_text = raw_text[3:]
            if raw_text.endswith("```"): raw_text = raw_text[:-3]
            return json.loads(raw_text.strip())
        except Exception as e:
            continue
    return None

# --- TELEGRAM CHATBOT HANDLERS ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🤖 *AI TRADING CHATBOT IS ONLINE!* 🚀\n\n"
        "මම තමා ඔයාගේ Trading Assistant. මගෙන් මෙන්න මේවා අහන්න පුළුවන්:\n\n"
        "🔹 `/scan` - TOP Coins 4ම Scan කරලා setups ගන්න.\n"
        "🔹 *BTC, ETH, SOL* වගේ Coin Name එකක් Direct Message කරන්න (e.g. `BTC` හෝ `Analyze SOL`).\n"
        "🔹 `/help` - Commands බලාගන්න."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 *Market Scan ආරම්භ කළා... විනාඩියක් දෙන්න!*", parse_mode="Markdown")
    
    brain = load_brain()
    all_data = fetch_all_market_data()
    
    long_setups, short_setups = [], []

    for symbol, mtf_data in all_data.items():
        res = analyze_single_coin(symbol, mtf_data, brain)
        if res and res.get("score", 0) >= 70:
            if res.get("decision") == "LONG": long_setups.append(res)
            elif res.get("decision") == "SHORT": short_setups.append(res)

    msg = "🚀 *TOP 4 COINS SCAN RESULT* 🚀\n=========================\n\n"
    msg += "🟢 *BUY / LONG OPPORTUNITIES*\n"
    if long_setups:
        for s in long_setups:
            msg += f"• *{s['symbol']}* | Score: *{s['score']}%*\n  Entry: ${s['entry']} | SL: ${s['sl']} | TP: ${s['tp']}\n  💡 _{s['reason']}_\n\n"
    else: msg += "  _No High Confidence Buy Setups_\n\n"

    msg += "🔴 *SELL / SHORT OPPORTUNITIES*\n"
    if short_setups:
        for s in short_setups:
            msg += f"• *{s['symbol']}* | Score: *{s['score']}%*\n  Entry: ${s['entry']} | SL: ${s['sl']} | TP: ${s['tp']}\n  💡 _{s['reason']}_\n\n"
    else: msg += "  _No High Confidence Sell Setups_\n\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper().strip()
    
    # Text එකෙන් Coin Symbol එක හොයාගැනීම (e.g., BTC, ETH, SOL, BNB)
    all_data = fetch_all_market_data()
    matched_symbol = None

    for sym in all_data.keys():
        clean_sym = sym.replace("USDT", "")
        if clean_sym in text or sym in text:
            matched_symbol = sym
            break

    if matched_symbol:
        await update.message.reply_text(f"⏳ *{matched_symbol}* technical setup එක analyze කරනවා...", parse_mode="Markdown")
        brain = load_brain()
        res = analyze_single_coin(matched_symbol, all_data[matched_symbol], brain)

        if res:
            decision_emoji = "🟢" if res.get("decision") == "LONG" else "🔴"
            reply = (
                f"{decision_emoji} *ANALYSIS FOR {res['symbol']}*\n"
                f"-----------------------------------\n"
                f"🎯 *Decision:* {res.get('decision')} ({res.get('score')}% Confidence)\n"
                f"📍 *Entry Price:* ${res.get('entry')}\n"
                f"🛡️ *Stop Loss:* ${res.get('sl')}\n"
                f"🎯 *Take Profit:* ${res.get('tp')}\n"
                f"💡 *Reason:* _{res.get('reason')}_"
            )
            await update.message.reply_text(reply, parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ Analysis එක ලබා ගැනීමට අපොහොසත් වුණා. නැවත උත්සාහ කරන්න.")
    else:
        await update.message.reply_text("🤖 මට තේරුණේ නෑ මචන්! Coin එකක නමක් (e.g. `BTC`, `ETH`) එවන්න, නැතනම් `/scan` ගහන්න.")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 LAUNCHING TELEGRAM AI TRADING CHATBOT...")
    print("=" * 60)

    connect_ai()

    # python-telegram-bot Application Setup
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers Add කිරීම
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("scan", scan_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("✅ Chatbot Ready! Open Telegram and talk to your Bot.")
    app.run_polling()