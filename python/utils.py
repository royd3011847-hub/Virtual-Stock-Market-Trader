from matplotlib import ticker
import yfinance as yf
import pandas as pd
from datetime import datetime, time, timedelta
import pandas_market_calendars as mcal
import pytz

#functions that I'm not using but might use later

def percent_return(ticker_symbol, period="1y"):
    prices = yf.Ticker(ticker_symbol).history(period=period)

    if prices.empty:
        return 0.0
    
    #generate a list of percent changes
    daily_returns = prices["Close"].pct_change().dropna()

    #calculate total return over the period
    returns_multiplier = daily_returns.add(1).prod()
    return (returns_multiplier - 1) * 100

def percent_price_change(ticker_symbol, period="1y"):
    prices = yf.Ticker(ticker_symbol).history(period=period)

    if prices.empty:
        return 0.0
    
    start_price = prices["Close"].iloc[0]
    end_price = prices["Close"].iloc[-1]

    print("start price: {}, end price: {}".format(start_price, end_price))

    percent_change = ((end_price - start_price) / start_price) * 100
    return percent_change

def percent_return_between(ticker_symbol, start, end):
    prices = yf.Ticker(ticker_symbol).history(start=start, end=end)

    if prices.empty:
        return 0.0

    close = prices["Close"]
    return (close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100

#functions that I'm using

def get_current_price(ticker_symbol):
    now = datetime.now().time()
    market_open = time(9, 30)
    market_close = time(16, 0)

    ticker = yf.Ticker(ticker_symbol)

    if market_open <= now <= market_close:
        prices = ticker.history(period="1d", interval="1m")
    else:
        prices = ticker.history(period="1d")

    if prices.empty:
        return None

    return float(prices["Close"].iloc[-1])


def get_price_at_time(ticker_symbol, date):
    # Convert input string to a pandas Timestamp
    time = pd.to_datetime(date)
    stock = yf.Ticker(ticker_symbol)
    
    # Determine search window and interval based on input length
    if len(date) <= 10:  # Daily data ('YYYY-MM-DD')
        start = time - pd.Timedelta(days=7)
        end = time + pd.Timedelta(days=7)
        interval = "1d"
    else:                # Intraday data ('YYYY-MM-DD HH:MM')
        start = time - pd.Timedelta(hours=1)
        end = time + pd.Timedelta(hours=1)
        interval = "1m"

    hist = stock.history(start=start, end=end, interval=interval)

    if hist.empty:
        return None

    # If the stock data is timezone-aware, we must make our 'time' variable match it
    if hist.index.tz is not None:
        if time.tzinfo is None:
            # Localize naive 'time' to the data's timezone
            time = time.tz_localize(hist.index.tz)
        else:
            # If 'time' already has a timezone, convert it to the data's timezone
            time = time.tz_convert(hist.index.tz)

    # Get the index of the closest timestamp
    idx = hist.index.get_indexer([time], method="nearest")
    
    # Check if index is valid (get_indexer returns -1 if no match found)
    if idx[0] == -1:
        return None
        
    return float(hist.iloc[idx[0]]["Close"])


def get_time_now():
    return datetime.utcnow().isoformat()

def _previous_and_current_close(ticker: str):
    stock = yf.Ticker(ticker)

    # Get recent daily data
    hist = stock.history(period="5d", interval="1d")

    if hist.empty or len(hist) < 2:
        return None, None

    # Last row = most recent trading day
    current_close = hist.iloc[-1]["Close"]
    previous_close = hist.iloc[-2]["Close"]

    return previous_close, current_close

def change_from_previous_close(ticker: str):
    prev_close, current_close = _previous_and_current_close(ticker)

    if prev_close is None:
        return None
    return round(current_close - prev_close, 2)



def percent_change_from_previous_close(ticker: str):
    prev_close, current_close = _previous_and_current_close(ticker)

    if prev_close is None or prev_close == 0:
        return None

    return round(((current_close - prev_close) / prev_close) * 100, 2)

def money_to_shares(money: float, ticker: str):
    current_price = get_current_price(ticker)
    if current_price is None or current_price == 0:
        return 0
    return (money / current_price)

def money_to_shares_at_time(money: float, ticker: str, date: str):
    price_at_time = get_price_at_time(ticker, date)
    if price_at_time is None or price_at_time == 0:
        return 0
    return (money / price_at_time)

def is_market_open_calendar(check_date):
    """
    Returns True if the NYSE is open on the given date.

    Parameters:
        check_date (date | datetime | str): Date to check (YYYY-MM-DD)

    Returns:
        bool
    """

    # Normalize input
    if isinstance(check_date, str):
        check_date = datetime.strptime(check_date, "%Y-%m-%d").date()
    elif isinstance(check_date, datetime):
        check_date = check_date.date()

    # Get trading schedule for that single day
    schedule = NYSE.schedule(
        start_date=check_date,
        end_date=check_date
    )

    return not schedule.empty

NYSE = mcal.get_calendar("NYSE")
EASTERN = pytz.timezone("US/Eastern")

def nearest_past_market_open_date(input_date):
    """
    Returns the nearest past date (including the given date)
    on which the NYSE was open.

    Parameters:
        input_date (date | datetime | str): Date to check (YYYY-MM-DD)

    Returns:
        date
    """

    # Normalize input
    if isinstance(input_date, str):
        input_date = datetime.strptime(input_date, "%Y-%m-%d").date()
    elif isinstance(input_date, datetime):
        input_date = input_date.date()

    # Quick check: is the market open on this date?
    if not NYSE.schedule(start_date=input_date, end_date=input_date).empty:
        return input_date

    # Walk backwards until an open market day is found
    check_date = input_date - timedelta(days=1)

    while True:
        schedule = NYSE.schedule(
            start_date=check_date,
            end_date=check_date
        )

        if not schedule.empty:
            return check_date

        check_date -= timedelta(days=1)

def nearest_past_market_close_datetime(input_date):
    """
    Returns:
        datetime (UTC) of market close on nearest past open market day
    """

    market_date = nearest_past_market_open_date(input_date)

    schedule = NYSE.schedule(
        start_date=market_date,
        end_date=market_date
    )

    if schedule.empty:
        raise RuntimeError("Market calendar returned no data for a valid trading day")

    close_time_utc = schedule.iloc[0]["market_close"]

    # Convert to naive UTC datetime (IMPORTANT)
    return close_time_utc.tz_convert("UTC").to_pydatetime().replace(tzinfo=None)