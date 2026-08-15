def calculate_trade_risk(
    account_balance: float,
    risk_percentage: float,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    trade_type: str = "SHORT",
):
    """
    Trade එකකට අදාළ Risk Amount, Position Size, සහ Risk-to-Reward Ratio (RR) ගණනය කරයි.
    """
    risk_amount = account_balance * (risk_percentage / 100)

    if trade_type.upper() == "LONG":
        sl_distance = entry_price - stop_loss
        tp_distance = take_profit - entry_price
    else:  # SHORT
        sl_distance = stop_loss - entry_price
        tp_distance = entry_price - take_profit

    if sl_distance <= 0:
        raise ValueError("Invalid Stop Loss price for the given trade direction!")

    sl_percentage = (sl_distance / entry_price) * 100
    position_size_usd = risk_amount / (sl_percentage / 100)
    rr_ratio = tp_distance / sl_distance

    return {
        "risk_amount_usd": round(risk_amount, 2),
        "position_size_usd": round(position_size_usd, 2),
        "sl_percentage": round(sl_percentage, 2),
        "rr_ratio": round(rr_ratio, 2),
        "is_valid_setup": rr_ratio >= 2.0,  # Minimum 1:2 RR Requirement
    }


def format_risk_analysis(risk_data):
    formatted = "=== RISK ENGINE PARAMETERS ===\n"
    formatted += f"Max Risk Amount    : ${risk_data['risk_amount_usd']}\n"
    formatted += f"Position Size (USD): ${risk_data['position_size_usd']}\n"
    formatted += f"Stop Loss Distance : {risk_data['sl_percentage']}%\n"
    formatted += f"Risk-to-Reward (RR): 1:{risk_data['rr_ratio']}\n"
    formatted += f"Setup Valid (RR>=2): {'✅ YES' if risk_data['is_valid_setup'] else '❌ NO (RR too low)'}\n"
    return formatted


if __name__ == "__main__":
    # Test Run
    result = calculate_trade_risk(
        account_balance=1000,
        risk_percentage=1,
        entry_price=63000,
        stop_loss=63500,
        take_profit=61500,
        trade_type="SHORT",
    )
    print(format_risk_analysis(result))