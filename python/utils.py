from matplotlib import ticker
import yfinance as yf
import pandas as pd
from datetime import datetime, time, timedelta
import pandas_market_calendars as mcal
import pytz

ETF_TICKERS = sorted([
    # S&P 500 and related ETFs
"VOO","SPY","IVV","VTI","SPLG","SPLV","SPYG","SPYD","SPYV","SPYX","SPYQ","SPYB","SPYI","SPYJ","SPYF","SPYH","SPYW","SPYY","SPYZ"
    # Dow Jones and related ETFs
"DIA","IYY","IWB","IWD","IWF","IWM","IWN","IWO","IWP","IWR","IWS","IWT","IWW","IWX",
    # QQQ and related ETFs
"QQQ","TQQQ","SQQQ","QLD","QID","QQQM","QQQX","QQQE","QQQG","QQQY","QQQZ","QQQS",
    # Volatility and related ETFs
"VUG","VTV","VOE","VBR","VOT","VXF","VV","VB","VEA","VWO","VNQ","VYM",
    # Bond ETFs
"VTIP","BND","BNDX","AGG","LQD","HYG","JNK","SHY","IEI","IEF","TLT","MBB","EMB","BIV","BLV","BNDW","BSV"
])

RUSSELL_2000_TICKERS = sorted([
    # Russell 2000 indices
    "RUT","RUI","RUA"
])

MUTUAL_FUND_TICKERS = sorted([
    # Vanguard mutual funds
    "VTSAX","VFIAX","VIMAX","VSMAX","VEXAX","VEMPX","VMCIX","VMGIX","VMGRX","VMRIX",
    # Schwab mutual funds
    "SWPPX","SWTSX","SWISX","SWSSX","SWTSX", "SWVXX", "SWAGX", "SWASX", "SWBIX", "SWGXX",
    # Fidelity mutual funds
    "FXAIX","FXNAX","FXSIX","FXSTX","FXUSX","FZROX", "FBGRX", "FSKAX", "FBALX"
    # Other popular mutual funds
])

#functions that I'm not using but might use later

def percent_return(ticker_symbol, period="1y"):
    prices = yf.Ticker(ticker_symbol).history(period=period)

    if prices.empty:
        return 0.0
    
    daily_returns = prices["Close"].pct_change().dropna()

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

def round_down_dollar(amount: float):
    """_rounds down a dollar amount to two decimal places
    Args:
        amount (float): _amount to round

    Returns:
        float: _rounded amount
    """
    return float(int(amount * 100)) / 100.0

def get_current_price(ticker_symbol):
    """_gets the current price of a stock ticker

    Args:
        ticker_symbol (str): _symbol

    Returns:
        float: _current price of the stock
    """
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
    """_gets the stock price of a ticker at a specific date

    Args:
        ticker (str): _ticker symbol
        date_str (str): _date in 'YYYY-MM-DD' format

    Returns:
        float: _price of the stock on the given date, or None if not available
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
    """_gets the previous and current closing prices for a ticker

    Args:
        ticker (str): _ticker symbol

    Returns:
        tuple: (previous_close, current_close): 
            previous_close (float): _closing price of the previous market day
            current_close (float): _closing price of the current market day
    """
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
    """_gets the amount change of a stock from the previous market days close

    Args:
        ticker (str): _ticker symbol

    Returns:
        float: _amount change of the stock from the previous market day's close
    """
    prev_close, current_close = _previous_and_current_close(ticker)

    if prev_close is None:
        return None
    return current_close - prev_close



def percent_change_from_previous_close(ticker: str):
    """_gets the percent change of a stock from the previous market days close

    Args:
        ticker (str): _ticker symbol

    Returns:
        float: _percent change of the stock from the previous market day's close, or None if not available
    """
    prev_close, current_close = _previous_and_current_close(ticker)

    if prev_close is None or prev_close == 0:
        return None

    return ((current_close - prev_close) / prev_close) * 100

def money_to_shares(money: float, ticker: str):
    """_gets the amount of shares of a stock given an amount of money

    Args:
        money (float): _amount of money
        ticker (str): _ticker symbol

    Returns:
        float: _number of shares that can be purchased with the given amount of money
    """
    current_price = get_current_price(ticker)
    if current_price is None or current_price == 0:
        return 0
    return (money / current_price)

def is_ETF(ticker):
    """_Checks if a ticker is in the list of banned tickers

    Args:
        ticker (str): _ticker symbol

    Returns:
        bool: True if the ticker is in the banned list, False otherwise
    """
    return ticker.upper() in ETF_TICKERS

def is_russell_2000(ticker):
    """_Checks if a ticker is in the list of Russell 2000 tickers

    Args:
        ticker (str): _ticker symbol
        
    Returns:
        bool: True if the ticker is in the Russell 2000 list, False otherwise
    """
    return ticker.upper() in RUSSELL_2000_TICKERS

def is_mutual_fund(ticker):
    """_Checks if a ticker is in the list of Mutual Fund tickers

    Args:
        ticker (str): _ticker symbol
    """
    return ticker.upper() in MUTUAL_FUND_TICKERS

def is_banned_prefix(ticker):
    banned_prefixes = ("SCH", "VOO", "SPY", "IVV", "VTI", "QQQ", "IWM", "DIA")
    return ticker.startswith(banned_prefixes)
# def money_to_shares_at_time(money: float, ticker: str, date: str):
#     price_at_time = get_price_at_time(ticker, date)
#     if price_at_time is None or price_at_time == 0:
#         return 0
#     return (money / price_at_time)

# Market calendar functions
NYSE = mcal.get_calendar("NYSE")



def is_market_open_calendar(check_date):
    """_Determines if date given is an open market day

    Args:
        check_date (str "YYYY-MM-DD"): _date to check

    Returns:
        bool: True if the market is open on the given date, False otherwise
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
    """_finds the most recent date that the market was open

    Args:
        check_date (str "YYYY-MM-DD"): _date to check

    Returns:
        date: The most recent market open date
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
    """_returns the datetime (UTC) of market close on the nearest past open market day
    if the input date is a market day, it returns the close time for that date

    Args:
        input_date (str "YYYY-MM-DD"): _date to check

    Returns:
        datetime (UTC): The UTC datetime of market close for the nearest past open market day
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
    """_gets the closest upcoming market open day
    if the input date is a market day, it returns that date

    Args:
        input_date (str "YYYY-MM-DD"): _date to check

    Returns:
        date: The closest upcoming market open date
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
    """_returns the datetime (UTC) of market close on the nearest future open market day
    if the input date is a market day, it returns the close time for that date

    Args:
        input_date (str "YYYY-MM-DD"): _date to check

    Returns:
        datetime (UTC): The UTC datetime of market close for the nearest future open market day
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

