import pandas as pd


def calculate_fibonacci_levels(df):
    """
    High සහ Low values මත පදනම්ව Fibonacci Retracement levels ගණනය කරයි.
    """
    recent_high = df["high"].max()
    recent_low = df["low"].min()
    diff = recent_high - recent_low

    fib_levels = {
        "swing_high": round(recent_high, 2),
        "swing_low": round(recent_low, 2),
        "fib_0": round(recent_high, 2),
        "fib_0.236": round(recent_high - (0.236 * diff), 2),
        "fib_0.382": round(recent_high - (0.382 * diff), 2),
        "fib_0.500": round(recent_high - (0.500 * diff), 2),
        "fib_0.618": round(recent_high - (0.618 * diff), 2),
        "fib_0.786": round(recent_high - (0.786 * diff), 2),
        "fib_1.000": round(recent_low, 2),
    }

    return fib_levels


def format_fib_for_ai(fib_levels):
    formatted = "=== FIBONACCI RETRACEMENT LEVELS ===\n"
    formatted += f"Swing High: {fib_levels['swing_high']} | Swing Low: {fib_levels['swing_low']}\n"
    formatted += f"0.236 Level : {fib_levels['fib_0.236']}\n"
    formatted += f"0.382 Level : {fib_levels['fib_0.382']}\n"
    formatted += f"0.500 Level : {fib_levels['fib_0.500']}\n"
    formatted += f"0.618 Golden Pocket : {fib_levels['fib_0.618']}\n"
    formatted += f"0.786 Level : {fib_levels['fib_0.786']}\n"
    return formatted