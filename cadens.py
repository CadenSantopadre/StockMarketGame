import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import yfinance as yf

# 1. Turn on interactive mode
plt.ion()

# 2. Define portfolio holdings (Ticker: Share Count)
portfolio_holdings = {"AAPL": 10, "MSFT": 5}
tickers = list(portfolio_holdings.keys())

# State variable to track what is currently being viewed
# Options: 'AAPL', 'MSFT', or 'PORTFOLIO'
current_view = "PORTFOLIO"


# 3. Define button callback functions
def switch_to_aapl(event):
    global current_view
    current_view = "AAPL"


def switch_to_msft(event):
    global current_view
    current_view = "MSFT"


def switch_to_portfolio(event):
    global current_view
    current_view = "PORTFOLIO"


# 4. Create the main figure window
# Adjusting subplots to leave room on the left side for buttons
fig, ax = plt.subplots(figsize=(10, 6))
plt.subplots_adjust(left=0.25)  # Shifts the main chart right to make space

# 5. Position and create UI Buttons
ax_btn_aapl = plt.axes([0.05, 0.7, 0.15, 0.075])  # [left, bottom, width, height]
ax_btn_msft = plt.axes([0.05, 0.55, 0.15, 0.075])
ax_btn_port = plt.axes([0.05, 0.4, 0.15, 0.075])

btn_aapl = Button(ax_btn_aapl, "View AAPL", color="lightgray", hovercolor="skyblue")
btn_msft = Button(ax_btn_msft, "View MSFT", color="lightgray", hovercolor="skyblue")
btn_port = Button(
    ax_btn_port, "View Portfolio", color="lightgreen", hovercolor="green"
)

# Connect buttons to their click events
btn_aapl.on_clicked(switch_to_aapl)
btn_msft.on_clicked(switch_to_msft)
btn_port.on_clicked(switch_to_portfolio)

print("Dashboard running. Click buttons in the GUI window to switch views.")

try:
    while True:
        # Fetch data for all assets in the portfolio
        # Group downloading is faster and uses fewer API hits
        raw_data = yf.download(
            tickers=tickers, period="1d", interval="1m", progress=False
        )

        if not raw_data.empty:
            ax.clear()

            # Separate out the Closing prices
            close_prices = raw_data["Close"]

            if current_view == "PORTFOLIO":
                # Calculate total historical value of the portfolio at every minute mark
                # (AAPL_Price * 10) + (MSFT_Price * 5)
                portfolio_value = (
                    close_prices["AAPL"] * portfolio_holdings["AAPL"]
                    + close_prices["MSFT"] * portfolio_holdings["MSFT"]
                )

                ax.plot(
                    portfolio_value.index,
                    portfolio_value,
                    color="darkgreen",
                    linewidth=2,
                )
                ax.set_title("Live Total Portfolio Value")
                ax.set_ylabel("Total Value ($)")

            elif current_view in tickers:
                # Plot the single selected ticker
                ticker_close = close_prices[current_view]
                ax.plot(
                    ticker_close.index, ticker_close, color="blue", linewidth=1.5
                )
                ax.set_title(f"Live {current_view} Stock Price")
                ax.set_ylabel("Price Per Share ($)")

            # Global Chart Styling
            ax.set_xlabel("Time")
            ax.grid(True, linestyle="--", alpha=0.5)
            fig.autofmt_xdate()  # Cleanly auto-rotates the timestamp labels

            # Force redraw on the active window canvas
            plt.draw()

        # Pause loop for 15 seconds before checking global state and fetching data again
        plt.pause(1)

except KeyboardInterrupt:
    print("Dashboard stopped.")

plt.ioff()
plt.show()
