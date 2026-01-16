import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px

def plot_stock(ticker_symbol, period="1y", interval="1d"):
    ticker = yf.Ticker(ticker_symbol)
    prices = ticker.history(period=period, interval=interval)

    if prices.empty:
        print("No data found.")
        return

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=prices.index,
            y=prices["Close"],
            mode="lines",
            name="Close Price"
        )
    )

    fig.update_layout(
        title=f"{ticker_symbol} Price ({period}, interval={interval})",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        template="plotly_white",
        hovermode="x unified"
    )

    fig.show()