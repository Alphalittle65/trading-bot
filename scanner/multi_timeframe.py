import pandas as pd
from data.binance_fetcher import get_market_data


def fetch_multi_tf_data(symbol="BTCUSDT", timeframes=None, limit=20):
    if timeframes is None:
        timeframes = ["15m", "1h", "4h", "1d"]

    mtf_data = {}

    for tf in timeframes:
        try:
            df = get_market_data(symbol=symbol, interval=tf, limit=limit)
            mtf_data[tf] = df
        except Exception as e:
            print(f"Error fetching {tf} data for {symbol}: {e}")

    return mtf_data


def format_mtf_data_for_ai(mtf_data):
    formatted_str = ""
    for tf, df in mtf_data.items():
        formatted_str += f"\n--- TIMEFRAME: {tf.upper()} (Last {len(df)} Candles) ---\n"
        # Display key columns
        formatted_str += df[["timestamp", "open", "high", "low", "close", "volume"]].to_string(index=False)
        formatted_str += "\n"

    return formatted_str


if __name__ == "__main__":
    print("⏳ Fetching Multi-Timeframe Data (15m, 1h, 4h, 1d)...")
    data = fetch_multi_tf_data("BTCUSDT")
    formatted = format_mtf_data_for_ai(data)
    print("✅ Multi-Timeframe Fetch Success!")
    print(formatted[:500] + "\n... (Data truncated for display)")