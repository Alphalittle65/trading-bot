from binance.client import Client
import pandas as pd


def get_market_data(symbol="BTCUSDT", interval="1h", limit=50):
    # Public endpoints සඳහා API Key අවශ්‍ය නොවේ
    client = Client()

    # Candlestick (Klines) Data ලබා ගැනීම
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)

    # Pandas DataFrame එකකට convert කිරීම
    df = pd.DataFrame(
        klines,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
            "ignore",
        ],
    )

    # අවශ්‍ය Columns ටික විතරක් තෝරා ගැනීම සහ Numeric වලට හරවා ගැනීම
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)

    return df


if __name__ == "__main__":
    # Test fetcher
    data = get_market_data("BTCUSDT", "1h", 5)
    print("✅ Binance Market Data Test Success!")
    print(data)