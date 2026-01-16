period
    amount of time
    ex:
        1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo

prices = ticker.history(period="1w")
    requests 1 week of historical price data
    returns a pandas dataframe
    rows: date index
    columns: Open, High, Low, Close, Volume, Dividends, Stock Splits
    price = ticker.history(period="1d", interval="1m")
        requests 1 day of historical price data with 1 minute intervals
    price = ticker.history(period="5d", interval="15m")
        requests 5 days of historical price data with 15 minute intervals



