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


def get_stock_price_date(ticker, date_str):
    """
    Get the closing price of a stock for the given trading day.
    Assumes the input date is a day when the market is open.
    
    Parameters:
    ticker (str): Stock ticker symbol (e.g., 'AAPL', 'GOOGL')
    date_str (str): Date in format 'YYYY-MM-DD' (should be a trading day)
    
    Returns:
    float: Closing price of the stock, or None if market was closed that day
    """
    try:
        # Parse the input date
        target_date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Fetch data for the specific day (plus one day for yfinance end parameter)
        end_date = target_date + timedelta(days=1)
        
        # Download stock data
        stock = yf.Ticker(ticker)
        data = stock.history(start=target_date.strftime('%Y-%m-%d'), 
                           end=end_date.strftime('%Y-%m-%d'))
        
        # Check if we got data for the requested date
        if data.empty:
            print(f"Market was closed on {date_str}")
            return None
        
        # Get the closing price
        close_price = data['Close'].iloc[0]
        
        return float(close_price)
    
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


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

# Market calendar functions
NYSE = mcal.get_calendar("NYSE")



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


def nearest_past_market_open_date(input_date):
    """
    Returns the nearest past date (including the given date)
    on which the NYSE was open.
    """

    # Normalize input
    if isinstance(input_date, str):
        input_date = datetime.strptime(input_date, "%Y-%m-%d").date()
    elif isinstance(input_date, datetime):
        input_date = input_date.date()

    # Walk backward until market is open
    check_date = input_date

    while not is_market_open_calendar(check_date):
        check_date -= timedelta(days=1)

    return check_date

def nearest_past_market_close_datetime(input_date):
    """
    Returns:
        datetime (UTC) of market close on nearest past open market day
    """

    market_date = nearest_past_market_open_date(input_date)
    print("nearest past market open date: {}".format(market_date))
    schedule = NYSE.schedule(
        start_date=market_date,
        end_date=market_date
    )

    if schedule.empty:
        raise RuntimeError("Market calendar returned no data for a valid trading day")

    close_time_utc = schedule.iloc[0]["market_close"]
    
    # Convert to naive UTC datetime (IMPORTANT)
    return close_time_utc.tz_convert("UTC").to_pydatetime().replace(tzinfo=None)
    
def nearest_future_market_open_date(input_date):
    """
    Returns the nearest future date (including the given date)
    on which the NYSE will be open.
    """

    # Normalize input
    if isinstance(input_date, str):
        input_date = datetime.strptime(input_date, "%Y-%m-%d").date()
    elif isinstance(input_date, datetime):
        input_date = input_date.date()

    # Walk forward until market is open
    check_date = input_date

    while not is_market_open_calendar(check_date):
        check_date += timedelta(days=1)

    return check_date

def nearest_future_market_close_datetime(input_date):
    """
    Returns:
        datetime (UTC) of market close on nearest future open market day
    """

    market_date = nearest_future_market_open_date(input_date)
    print("nearest future market open date: {}".format(market_date))
    schedule = NYSE.schedule(
        start_date=market_date,
        end_date=market_date
    )

    if schedule.empty:
        raise RuntimeError("Market calendar returned no data for a valid trading day")

    close_time_utc = schedule.iloc[0]["market_close"]
    
    # Convert to naive UTC datetime (IMPORTANT)
    return close_time_utc.tz_convert("UTC").to_pydatetime().replace(tzinfo=None)

def datetime_to_date(dt: datetime):
    return dt.date()
