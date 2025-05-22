from vnstock import Vnstock
from datetime import datetime
import pandas as pd


def get_stock_data(source, symbol, start_date, end_date):
    print("Getting stock from:", symbol)
    stock = Vnstock().stock(symbol=symbol, source=source)
    df = stock.quote.history(start=start_date, end=end_date, interval='1D')
    df['source'] = source
    df['symbol'] = symbol
    df = df.drop(columns=['high', 'low'])
    return df

if __name__ == "__main__":
    # Get current date in YYYY-MM-DD format
    current_date = datetime.now().strftime('%Y-%m-%d')
    stock_codes = [
        "VCB",
        "CTG",
        "VPB",
        "BID",
        "TCB",
        "HPG",
        "MWG",
        "VNM",
        "VIC",
        "FPT"
    ]
    source = "VCI"
    df = pd.DataFrame()
    for symbol in stock_codes:
        df = pd.concat([df, get_stock_data(source=source, symbol = symbol, start_date='2024-01-01' )])
    print(df)


