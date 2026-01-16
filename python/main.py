

from plotting import *
from utils import *
from models import *
#s and p ticker: 

portfolio1 = Portfolio(
    user_id=1,
    starting_money=30000.0,
    duration_days=3
)

print("Portfolio timer ends at: {}".format(portfolio1.end_date_time))
print("Seconds remaining: {}".format(portfolio1.seconds_remaining()))
print("Days remaining: {:.2f}".format(portfolio1.days_remaining()))
print("Timer status: {}".format(portfolio1.timer_status_string()))

print(nearest_past_market_close_datetime("2026-01-01"))

print(nearest_past_market_close_datetime("2026-07-04"))

print(nearest_past_market_close_datetime("2026-07-06"))

print(nearest_past_market_close_datetime("2026-09-16"))

# ticket1 = "AAPL"
# ticket2 = "MSFT"
# ticket3 = "GME"
# date = "2023-12-01"
# portfolio1.buy_holding(ticket1, money_to_shares(200, ticket1), get_current_price(ticket1))
# print("1--------------------------------")
# portfolio1.print_portfolio()
# portfolio1.buy_holding(ticket2, money_to_shares(200, ticket2), get_current_price(ticket2))
# print("2--------------------------------")
# portfolio1.print_portfolio()
# portfolio1.buy_holding(ticket1, money_to_shares(200, ticket1), get_current_price(ticket1))
# # print("money: {}".format(portfolio1.get_money()))
# print("3--------------------------------")
# portfolio1.print_portfolio()
# portfolio1.sell_holding_shares(ticket1, 0.5)
# print("4--------------------------------")
# portfolio1.print_portfolio()
# portfolio1.sell_holding_shares(ticket2, portfolio1.holding_shares(ticket2) / 2)
# print("5--------------------------------")
# portfolio1.print_portfolio()
# portfolio1.buy_holding(ticket1, money_to_shares(5000, ticket1), get_current_price(ticket1))
# print("6--------------------------------")
# portfolio1.print_portfolio()

print(is_market_open_calendar("2026-01-01"))  # False (New Year's Day)
print(is_market_open_calendar("2026-01-02"))  # True
print(is_market_open_calendar("2026-07-03"))  # False (observed July 4th)
print(is_market_open_calendar("2035-03-15"))  # True

print(nearest_past_market_open_date("2026-01-01"))  # 2025-12-31
print(nearest_past_market_open_date("2026-01-04"))  # 2026-01-02 (Saturday → Friday)
print(nearest_past_market_open_date("2026-07-04"))  # 2026-07-02 (holiday)
print(nearest_past_market_open_date("2026-07-06"))  # 2026-07-06 (already open)



# portfolio1.sell_all_holdings()
# print("--------------------------------")
# print(change_from_previous_close("RBLX"))
# print(percent_change_from_previous_close("RBLX"))
# print(change_from_previous_close("TSLA"))
# print(percent_change_from_previous_close("TSLA"))
# print(change_from_previous_close("GME"))
# print(percent_change_from_previous_close("GME"))
# print(change_from_previous_close("MSFT"))
# print(percent_change_from_previous_close("MSFT"))

# portfolio1.print_SNP()



#plot_stock("AAPL", period="6mo", interval="1d")

#python\main.py

#to run with venv:
# python python\main.py

