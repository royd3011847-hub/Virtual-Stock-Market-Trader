from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import JSON
from sqlalchemy.ext.mutable import MutableDict
from datetime import datetime, timedelta, date, time, timezone
from zoneinfo import ZoneInfo


from .utils import *

db = SQLAlchemy()

# Define User and Portfolio models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    Portfolio = db.relationship('Portfolio', backref='owner', uselist=False)
    # helper methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Portfolio model to track user holdings
class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    starting_money = db.Column(db.Float, default=100000.0)
    money = db.Column(db.Float)
    holdings = db.Column(MutableDict.as_mutable(JSON), nullable=False, default=dict)
    duration_days = db.Column(db.Integer, nullable=False)
    end_date_time = db.Column(db.DateTime, nullable=True)
    SNP_Shares = db.Column(db.Float, default=0.0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.money = self.starting_money
        
        #set SNP shares based on starting money
        if(get_current_price("^GSPC") is None):
            raise ValueError("Could not retrieve S&P 500 price. Please try again later.")
        SNP_price = get_current_price("^GSPC")
        self.SNP_Shares = self.starting_money / SNP_price
        
        self.set_timer_end_date()

    def get_money(self):
        return round_down_dollar(self.money)
    
    # View Totals from holdings --------------------------------------------------
    def view_current_stock_price(self, ticker):
        return get_current_price(ticker)
    
    def total_value(self):
        total = self.money
        for ticker, data in self.holdings.items():
            total += get_current_price(ticker) * data['shares']
        return round_down_dollar(total)
    
    def total_invested(self):
        total = 0.0
        for ticker, data in self.holdings.items():
            total += data['price_bought'] * data['shares']
        return round_down_dollar(total)
    
    def total_profit_gain(self):
        return self.total_value() - self.starting_money    
    
    def total_profit_gain_percent(self):
        if self.starting_money == 0:
            return 0.0
        return (self.total_profit_gain() / self.starting_money * 100)
    
    #view Individual Holdings --------------------------------------------------

    def holding_shares(self, ticker):
        if ticker not in self.holdings:
            return 0.0
        data = self.holdings[ticker]
        return data['shares']
    
    def holding_value(self, ticker):
        if ticker not in self.holdings:
            return 0.0
        
        if(self.is_timer_expired()):
            price = self.get_price_at_end_date(ticker)
        else:
            price = get_current_price(ticker)
        
        return price * self.holding_shares(ticker)
    
    def todays_holding_percent_gain(self, ticker):
        if ticker not in self.holdings:
            return 0.0
        return percent_change_from_previous_close(ticker)
    
    def todays_holding_profit(self, ticker):
        if ticker not in self.holdings:
            return 0.0
        return round_down_dollar(change_from_previous_close(ticker) * self.holdings[ticker]['shares'])
    
    def holding_profit(self, ticker):
        if ticker not in self.holdings:
            return 0.0
        if self.is_timer_expired():
            price = self.get_price_at_end_date(ticker)
        else:
            price = get_current_price(ticker)
        data = self.holdings[ticker]
        invested_amount = data['price_bought'] * data['shares']
        current_value = price * data['shares']
        return current_value - invested_amount
    
    def holding_profit_gain_percent(self, ticker):
        if ticker not in self.holdings:
            return 0.0
        if self.is_timer_expired():
            price = self.get_price_at_end_date(ticker)
        else:
            price = get_current_price(ticker)
        data = self.holdings[ticker]
        invested_amount = data['price_bought'] * data['shares']
        current_value = price * data['shares']
        if invested_amount == 0:
            return 0.0
        return (current_value - invested_amount) / invested_amount * 100
    
    def holding_percent_of_portfolio(self, ticker):
        if ticker not in self.holdings:
            return 0.0
        total_value = self.total_value()
        if total_value == 0:
            return 0.0
        holding_value = self.holding_value(ticker)
        return (holding_value / total_value) * 100
    

    #view SNP Value --------------------------------------------------
    def SNP_shares(self):
        return self.SNP_Shares

    def SNP_value(self):
        current_price = get_current_price("^GSPC")
        return current_price * self.SNP_Shares
    
    def SNP_profit(self):
        if self.is_timer_expired():
            price = self.get_price_at_end_date("^GSPC")
        else:
            price = get_current_price("^GSPC")
        return (price * self.SNP_Shares - self.starting_money)
    
    def SNP_profit_percent(self):
        if self.is_timer_expired():
            price = self.get_price_at_end_date("^GSPC")
        else:
            price = get_current_price("^GSPC")
        return ((price * self.SNP_Shares - self.starting_money) / self.starting_money) * 100
    
    def SNP_price(self):
        return get_current_price("^GSPC")
    
    def SNP_todays_percent_gain(self):
        return percent_change_from_previous_close("^GSPC")
    
    def SNP_todays_profit_gain(self):
        return change_from_previous_close("^GSPC") * self.SNP_Shares
    
    def value_minus_SNP_value(self):
        if self.is_timer_expired():
            price = self.get_price_at_end_date("^GSPC")
            SNP_value = price * self.SNP_Shares
            return self.total_value() - SNP_value
        return self.total_value() - self.SNP_value()
    
    def SNP_value_difference_percent(self):
        SNP_value = self.SNP_value()
        if SNP_value == 0:
            return 0.0
        if self.is_timer_expired():
            price = self.get_price_at_end_date("^GSPC")
            SNP_value = price * self.SNP_Shares
        return (self.total_value() - SNP_value) / SNP_value * 100

    #timer logic --------------------------------------------------
    def set_timer_end_date(self):
        current_time = datetime.utcnow()
        end_date_holder = current_time + timedelta(days=self.duration_days-1)
        # FULL datetime, not date-only
        result = nearest_past_market_close_datetime(end_date_holder)
        if(result < current_time):
            result = nearest_future_market_close_datetime(end_date_holder)
        self.end_date_time = result
        
            
    
    def seconds_remaining(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if self.is_timer_expired():
            return 0

        # Convert end_date_time to datetime if it's a date
        end_dt = self.end_date_time
        if isinstance(end_dt, date) and not isinstance(end_dt, datetime):
            end_dt = datetime.combine(end_dt, time(16, 0))
        
        delta = end_dt - now
        return max(0, int(delta.total_seconds()))
    


    def days_remaining(self):
        return self.seconds_remaining() / 86400


    def is_timer_expired(self):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Convert end_date_time to datetime if it's a date
        end_dt = self.end_date_time
        if isinstance(end_dt, date) and not isinstance(end_dt, datetime):
            end_dt = datetime.combine(end_dt, time(16, 0))
        
        return now >= end_dt


    def timer_status_string(self):
        if self.is_timer_expired():
            return "Timer expired"
        
        seconds = self.seconds_remaining()
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        return f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes remaining"

    def get_end_date_time_string(self):
        if self.end_date_time is None:
            return ""

        utc_dt = self.end_date_time.replace(tzinfo=timezone.utc)

        cst_dt = utc_dt.astimezone(ZoneInfo("America/Chicago"))

        return cst_dt.strftime("%Y-%m-%d %I:%M:%S %p CST")

    
    def get_price_at_end_date(self, ticker):
        if self.end_date_time is None:
            raise ValueError("End date time is not set.")
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if (self.end_date_time > now):
            raise ValueError("End date time is in the future.")
        return get_stock_price_date(ticker, str(datetime_to_date(self.end_date_time)))

    #Manage holdings --------------------------------------------------
    def sort_holdings_by_value(self):
        if not self.holdings:
            return
        sorted_holdings = dict(
            sorted(self.holdings.items(),
            key=lambda item: get_current_price(item[0]) * item[1]['shares'],
            reverse=True))
        self.holdings = sorted_holdings
        self.print_portfolio()
    
    def buy_holding(self, ticker, shares, price_bought):
        if self.money - (shares * price_bought) < 0:
            raise ValueError("Insufficient funds to buy holdings.")
        self.money -= shares * price_bought

        if not self.holdings:
            self.holdings = {}

        if ticker in self.holdings:
            current_shares = self.holdings[ticker]["shares"]
            current_price = self.holdings[ticker]["price_bought"]
            total_shares = current_shares + shares
            avg_price = ((current_price * current_shares) + (price_bought * shares)) / total_shares
            del self.holdings[ticker]
            self.holdings[ticker] = {
                "shares": total_shares,
                "price_bought": avg_price,
            }
        else:
            self.holdings[ticker] = {
                "shares": shares,
                "price_bought": price_bought,
            }
        self.sort_holdings_by_value()
        
    def sell_holding(self, ticker):
        if ticker not in self.holdings:
            raise ValueError("No holdings to sell.")

        current_price = get_current_price(ticker)
        shares = self.holdings[ticker]["shares"]
        self.money += shares * current_price
        del self.holdings[ticker]
        self.sort_holdings_by_value()

    def sell_holding_shares(self, ticker, shares):
        if ticker not in self.holdings or self.holdings[ticker]["shares"] < shares - 0.001:
            raise ValueError("Insufficient shares to sell.")
        
        if (self.holdings[ticker]["shares"] - shares) <= 0.0003:
            self.sell_holding(ticker)
        else:
            price_bought_holder = self.holdings[ticker]["price_bought"]
            shares_holder = self.holdings[ticker]["shares"]
            current_price = get_current_price(ticker)

            self.money += shares * current_price
            del self.holdings[ticker]
            self.holdings[ticker] = {
                "shares": shares_holder - shares,
                "price_bought": price_bought_holder,
            }
        self.sort_holdings_by_value()

    
    def sell_all_holdings(self):
        if not self.holdings:
            return
        for ticker in list(self.holdings.keys()):
            self.sell_holding(ticker)

    
    def clear_holdings(self):
        self.holdings = {}

    #print representations --------------------------------------------------
    def __repr__(self):
        return f"<Portfolio user_id={self.user_id} holdings={self.holdings_to_string()} money={self.money} time_remaining={self.timer_status_string()}>"
    
    def holdings_to_string(self):
        return ", ".join([f"{ticker}: {data['shares']} shares at ${data['price_bought']}\n" for ticker, data in self.holdings.items()])
    
    def print_holding(self, ticker):
        if ticker not in self.holdings:
            return f"{ticker}: No holdings."
        print("{}:".format(ticker))
        print("holding Value: {}".format(self.holding_value(ticker)))
        print("holding Shares: {}".format(self.holding_shares(ticker)))
        print("total holding Profit/Gain: {}".format(self.holding_profit(ticker)))
        print("total holding Profit/Gain %: {}".format(self.holding_profit_gain_percent(ticker)))
        print("Today's % Gain: {}".format(self.todays_holding_percent_gain(ticker)))
        print("Today's Profit/Gain: {}".format(self.todays_holding_profit(ticker)))
        print("Holding % of Portfolio: {}".format(self.holding_percent_of_portfolio(ticker)))
    
    def print_portfolio(self):
        print("Portfolio Summary:")
        print("Total Value: ${:.2f}".format(self.total_value()))
        print("Total Invested: ${:.2f}".format(self.total_invested()))
        print("Available Money: ${:.2f}".format(self.get_money()))
        print("Holdings:")
        for ticker in self.holdings:
            print(" - {}: {} value".format(ticker, self.holding_value(ticker)))
            
    def print_SNP(self):
        print("S&P 500:")
        print("SNP Value: {}".format(self.SNP_value()))
        print("SNP Shares: {}".format(self.SNP_shares()))
        print("Total SNP Profit/Gain: {}".format(self.SNP_profit()))
        print("Total SNP Profit/Gain %: {}".format(self.SNP_profit_percent()))
        print("Today's SNP % Gain: {}".format(self.SNP_todays_percent_gain()))
        print("Today's SNP Profit/Gain: {}".format(self.SNP_todays_profit_gain()))
        
