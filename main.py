import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from functools import partial

# Force interactive windowing
plt.ion()

# --- 1. CONFIGURATION & LEDGER ---
PORTFOLIO_LEDGER = [
    {"ticker": "DAL",  "shares": 175,  "date_acquired": "2026-10-06", "cost-basis": 84.07},
    {"ticker": "JPM",  "shares": 50,   "date_acquired": "2026-09-17", "cost-basis": 346.35},
    {"ticker": "MRK",  "shares": 15,   "date_acquired": "2026-09-21", "cost-basis": 149.81},
    {"ticker": "MRNA", "shares": 25,   "date_acquired": "2026-09-23", "cost-basis": 185.36}, 
    {"ticker": "MRNA", "shares": 40,   "date_acquired": "2026-09-17", "cost-basis": 160.79}, 
    {"ticker": "NVDA", "shares": 20,   "date_acquired": "2026-09-17", "cost-basis": 219.02},
    {"ticker": "PEP",  "shares": 15,   "date_acquired": "2026-10-05", "cost-basis": 124.82},
    {"ticker": "RCAT", "shares": 1000, "date_acquired": "2026-09-18", "cost-basis": 6.80},
    {"ticker": "SPCX", "shares": 60,   "date_acquired": "2026-09-17", "cost-basis": 155.83},
    {"ticker": "TSLA", "shares": -15,  "date_acquired": "2026-10-05", "cost-basis": 368.59},  # Short
    {"ticker": "TSM",  "shares": 20,   "date_acquired": "2026-09-17", "cost-basis": 424.50},
    {"ticker": "TTWO", "shares": 100,  "date_acquired": "2026-09-21", "cost-basis": 209.54},
]

tickers = sorted(list(set(item["ticker"] for item in PORTFOLIO_LEDGER)))
current_view = "PORTFOLIO"
cached_data = pd.DataFrame()  # Shared local database for real-time price ticks

# --- 2. CORE UPDATE & RENDER LOGIC ---
def update_plot():
    """Redraws the view instantly from memory cache when buttons are clicked."""
    global cached_data
    if cached_data.empty:
        return
        
    ax.clear()
    
    if "Close" in cached_data.columns:
        close_prices = cached_data["Close"]
        if isinstance(close_prices, pd.Series):
            close_prices = close_prices.to_frame(name=tickers)
    else:
        return

    if current_view == "PORTFOLIO":
        portfolio_pnl = pd.Series(0.0, index=close_prices.index)

        for item in PORTFOLIO_LEDGER:
            ticker = item["ticker"]
            shares = item["shares"]
            cost = item["cost-basis"]

            if ticker in close_prices.columns:
                ticker_close = close_prices[ticker]
                
                # Structural short position logic
                if shares < 0:
                    position_pnl = (cost - ticker_close) * abs(shares)
                else:
                    position_pnl = (ticker_close - cost) * shares
                    
                portfolio_pnl += position_pnl

        ax.plot(portfolio_pnl.index, portfolio_pnl, color="darkgreen", linewidth=2)
        ax.axhline(0, linestyle=":", color="black", alpha=0.6)
        ax.set_title("Live Portfolio Unrealized Gain/Loss")
        ax.set_ylabel("P&L ($)")

    elif current_view in tickers:
        if current_view in close_prices.columns:
            ticker_close = close_prices[current_view]
            ax.plot(ticker_close.index, ticker_close, color="blue", linewidth=1.5)
            
            matching_positions = [i for i in PORTFOLIO_LEDGER if i["ticker"] == current_view]
            
            for entry_idx, info in enumerate(matching_positions):
                label_suffix = f" (Lot {entry_idx+1})" if len(matching_positions) > 1 else ""
                pos_type = "Short" if info["shares"] < 0 else "Long"
                
                ax.axhline(info["cost-basis"], linestyle="--", alpha=0.7,
                           label=f"{pos_type}{label_suffix} Basis: ${info['cost-basis']:.2f}")
            
            ax.set_title(f"Live {current_view} Stock Price")
            ax.set_ylabel("Price Per Share ($)")
            ax.legend(loc="upper left")
    
    ax.set_xlabel("Time")
    ax.grid(True, linestyle="--", alpha=0.5)
    fig.autofmt_xdate()  
    fig.canvas.draw_idle()  # Force the UI window manager to repaint the frame immediately

def fetch_data_callback():
    """Background download task executed on an independent structural window interval."""
    global cached_data
    print("Fetching live market data payload...")
    raw_data = yf.download(tickers=tickers, period="1d", interval="1m", progress=False)
    if not raw_data.empty:
        cached_data = raw_data
        update_plot()

def switch(event, ticker):
    """Instantly modifies view states on button click event loops."""
    global current_view
    current_view = ticker
    update_plot()

# --- 3. UI BUILD & LAYOUT ---
fig, ax = plt.subplots(figsize=(12, 7))
plt.subplots_adjust(left=0.25)

left = 0.03
width = 0.18
height = 0.035
start_bottom = 0.92
spacing = 0.045

button_axes = {}
buttons = {}

# Main Portfolio Button
button_axes["PORTFOLIO"] = plt.axes([left, start_bottom, width, height])
buttons["PORTFOLIO"] = Button(button_axes["PORTFOLIO"], "TOTAL PORTFOLIO")
buttons["PORTFOLIO"].on_clicked(partial(switch, ticker="PORTFOLIO"))

# Ticker Buttons
for idx, ticker in enumerate(tickers):
    current_bottom = (start_bottom - spacing) - (idx * spacing)
    button_axes[ticker] = plt.axes([left, current_bottom, width, height])
    buttons[ticker] = Button(button_axes[ticker], ticker)
    buttons[ticker].on_clicked(partial(switch, ticker=ticker))

# --- 4. TIMER REGISTRATION & RUN ---
# Get baseline prices first before handing main thread context to the GUI container
fetch_data_callback()

# Attach an asynchronous interval clock directly onto the window framework canvas
timer = fig.canvas.new_timer(interval=15000)  # 15000ms = 15 seconds
timer.add_callback(fetch_data_callback)
timer.start()

plt.show(block=True)
