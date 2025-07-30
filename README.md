# Paper Trader (Indian Stocks)
 I came to know about stock markets but i don't have the money to invest till now so i created this application just to test my  investing and trading skills.
This is a web application for paper trading Indian stocks using live market data from Yahoo Finance (via yfinance). Users can buy and sell stocks, manage virtual funds, and view their portfolio performance in real time.I bet you guys will like the application after you know it has been built by a 16 y/o high school kid from India. Feel free to improvise and modify it with your own preferences

## Features
- **Buy/Sell Indian stocks** with virtual money
- **Live price updates** using yfinance
- **Portfolio dashboard** with holdings, returns, and summary
- **User authentication** (email, password, PIN)
- **Add funds** to your account
- **Friendly error messages** for invalid actions

## Folder Structure
```
trader_app/
    app.py                # Main Flask backend
    instance/
        database.db       # SQLite database (user data, ignored in git)
    static/
        css/
            style.css     # App styles
    templates/
        base.html         # Base template
        login.html        # Login/signup page
        portfolio.html    # Portfolio dashboard
        trade.html        # Buy/Sell/Manage funds page
```

## Setup Instructions

### 1. Clone the repository
```sh
git clone <your-repo-url>
cd Paper_trader/trader_app
```

### 2. Create a virtual environment (recommended)
```sh
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```sh
pip install -r requirements.txt
```

### 4. Run the app
```sh
python app.py
```

The app will start at `http://127.0.0.1:5000/`(or some different address shown in your terminal)

## Dependencies
- Flask
- Flask-SQLAlchemy
- Werkzeug
- yfinance
- pandas (required by yfinance)

See `requirements.txt` for details.

## Usage
- **Sign up** with email, password, and PIN
- **Add funds** to your account
- **Buy stocks** by entering symbol and quantity
- **Sell stocks** (only stocks you own, up to your holding)
- **View portfolio** for live updates and performance

## Example Screenshots
- Portfolio dashboard: ![Portfolio Screenshot](screenshots/portfolio.png)
- Trade page: ![Trade Screenshot](screenshots/trade.png)

## .gitignore
See `.gitignore` for ignored files (user data, database, venv, etc.)

---

**Note:** This is a paper trading app for educational purposes only. No real money or trading involved.
---

## Options Trading Module

This app has been updated to include a manual options-trading module, allowing users to track option positions alongside their stock holdings.

### How the New Feature Works

1.  **New "Orders" Tab**
    *   A new item named **"Orders"** is available in the sidebar.
    *   This page contains a form to create a new option position by manually entering the **Option Symbol**, **Buy Price**, and **Quantity**.
    *   Below the form is a **ledger of all option trades** (buys and sells) sorted in reverse-chronological order.

2.  **Closing a Position**
    *   In the Orders ledger, every open position has a **"Sell"** button.
    *   Clicking "Sell" opens a pop-up window (a modal) where you can enter the **Sell Price** and optional **Notes**.
    *   Upon submission, the order is marked as "closed", and the transaction is recorded in the ledger.

### Viewing Open Positions in Portfolio

*   In the **Portfolio** tab, a new section named **"Positions"** now appears at the top.
*   This section displays all currently **open** option positions.
*   Your existing stock **"Holdings"** list remains unchanged below the new positions section.

### Data Migration and Persistence

*   **No Data Loss:** All existing user data, including user accounts, funds, and stock trade history, is fully preserved.
*   **New Data Table:** The options trading feature uses a new `OptionOrder` table in the database. The existing `Trade` table for stocks is not modified.
*   **Migration Process:** The app is designed for a seamless upgrade. When you run the updated version for the first time, the application will automatically create the new `OptionOrder` table in the database without affecting any existing tables. No manual migration is needed.

### Configuration Changes

*   No configuration changes are required to enable this new feature.
