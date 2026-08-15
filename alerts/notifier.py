from datetime import datetime


def format_terminal_dashboard(
    symbol, bias, confidence, setup_name, entry_range, sl, tp1, tp2, risk_data
):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    dashboard = f"""
============================================================
🤖 AI TRADING AGENT - MASTER DASHBOARD | {now}
============================================================
COIN PAIR       : {symbol}
MARKET BIAS     : {bias}
CONFIDENCE SCORE: {confidence}%
CURRENT SETUP   : {setup_name}

------------------------------------------------------------
🎯 EXECUTION PLAN & LEVELS
------------------------------------------------------------
ENTRY ZONE      : {entry_range}
STOP LOSS (SL)  : {sl}
TAKE PROFIT 1   : {tp1}
TAKE PROFIT 2   : {tp2}

------------------------------------------------------------
🛡️ RISK ENGINE PARAMETERS ($1,000 Capital Base)
------------------------------------------------------------
MAX RISK (1%)   : ${risk_data['risk_amount_usd']}
POSITION SIZE   : ${risk_data['position_size_usd']}
SL DISTANCE     : {risk_data['sl_percentage']}%
R:R RATIO       : 1:{risk_data['rr_ratio']}
SETUP STATUS    : {'✅ APPROVED (Valid R:R)' if risk_data['is_valid_setup'] else '⚠️ REJECTED (Low R:R)'}
============================================================
"""
    return dashboard


def send_alert(message):
    # Standard Terminal Alert Box
    print("\n" + "🚨" * 20)
    print("      LIVE TRADE ALERT GENERATED      ")
    print("🚨" * 20)
    print(message)