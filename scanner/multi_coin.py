import ccxt
import pandas as pd

def fetch_all_market_data():
    exchange = ccxt.binance()
    
    # Market එකේ Volatility & Movement වැඩිම Top 4 Coins
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
    timeframes = ['15m', '1h', '4h']
    
    market_data = {}
    
    for symbol in symbols:
        coin_key = symbol.replace('/', '')
        market_data[coin_key] = {}
        
        for tf in timeframes:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe=tf, limit=100)
                df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                market_data[coin_key][tf] = df
            except Exception as e:
                print(f"⚠️ Error fetching {symbol} {tf}: {e}")
                
    return market_data