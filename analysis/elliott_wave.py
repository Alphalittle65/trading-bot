import pandas as pd


def detect_swing_points(df, window=3):
    df = df.copy()
    df["is_high"] = False
    df["is_low"] = False

    for i in range(window, len(df) - window):
        if df["high"].iloc[i] == df["high"].iloc[i - window : i + window + 1].max():
            df.loc[df.index[i], "is_high"] = True
        if df["low"].iloc[i] == df["low"].iloc[i - window : i + window + 1].min():
            df.loc[df.index[i], "is_low"] = True

    swings = []
    for idx, row in df.iterrows():
        if row["is_high"]:
            swings.append(("HIGH", row["high"], row["timestamp"]))
        elif row["is_low"]:
            swings.append(("LOW", row["low"], row["timestamp"]))

    return swings


def format_elliott_context(swings):
    formatted = "=== ELLIOTT WAVE SWING SEQUENCE (Recent Swings) ===\n"
    for swing_type, price, time in swings[-8:]:
        formatted += f"[{swing_type}] Price: {price} at {time}\n"
    return formatted