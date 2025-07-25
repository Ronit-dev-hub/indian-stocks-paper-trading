# In trading_app/app.py

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import yfinance as yf
from decimal import Decimal
import os

# --- APP CONFIGURATION ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    pin_hash = db.Column(db.String(150), nullable=False)
    funds = db.Column(db.Numeric(10, 2), default=0.00)
    trades = db.relationship('Trade', backref='owner', lazy=True)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    symbol = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    trade_type = db.Column(db.String(10), nullable=False, default='buy')

# --- HELPER FUNCTIONS ---
def get_current_price(symbol):
    """Fetches the current price for a single stock."""
    try:
        ticker = yf.Ticker(symbol + ".NS")
        data = ticker.history(period="1d")
        return Decimal(data['Close'].iloc[-1]) if not data.empty else None
    except Exception:
        return None

def get_live_market_data(symbols_ns):
    """Fetches detailed live market data for a list of symbols."""
    live_data = {}
    for symbol_ns in symbols_ns:
        try:
            ticker_info = yf.Ticker(symbol_ns).info
            current_price = ticker_info.get('regularMarketPrice')
            prev_close = ticker_info.get('previousClose')

            if current_price and prev_close:
                symbol = symbol_ns.replace('.NS', '')
                change = current_price - prev_close
                percent_change = (change / prev_close) * 100
                live_data[symbol] = {
                    'price': current_price,
                    'change': change,
                    'percent_change': percent_change
                }
        except Exception:
            continue
    return live_data

def get_portfolio_summary(user_id):
    """Calculates portfolio holdings from trades."""
    user_trades = Trade.query.filter_by(user_id=user_id).all()
    holdings = {}
    for trade in user_trades:
        if trade.symbol not in holdings:
            holdings[trade.symbol] = {'quantity': 0, 'total_cost': Decimal('0.0')}
        holdings[trade.symbol]['quantity'] += trade.quantity
        holdings[trade.symbol]['total_cost'] += Decimal(trade.quantity) * trade.price
    
    portfolio = {}
    for symbol, data in holdings.items():
        if data['quantity'] > 0:
            avg_price = data['total_cost'] / data['quantity']
            portfolio[symbol] = {
                'quantity': data['quantity'],
                'avg_price': avg_price.quantize(Decimal('0.01')),
                'invested_value': data['total_cost'].quantize(Decimal('0.01'))
            }
    return portfolio

# --- AUTHENTICATION ROUTES ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if 'user_id' in session and 'pin_verified' in session:
        return redirect(url_for('portfolio'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        pin = request.form.get('pin')
        user = User.query.filter_by(email=email).first()

        if 'check_pin' in request.form:
            if user and check_password_hash(user.pin_hash, pin):
                session['pin_verified'] = True
                return redirect(url_for('portfolio'))
            else:
                flash('Invalid PIN.', 'error')
        elif 'signup' in request.form:
            if user:
                flash('Email already exists.', 'error')
            else:
                new_user = User(
                    email=email,
                    password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
                    pin_hash=generate_password_hash(pin, method='pbkdf2:sha256')
                )
                db.session.add(new_user)
                db.session.commit()
                session['user_id'] = new_user.id
                flash('Account created! Please set your initial funds.', 'success')
                return redirect(url_for('trade'))
        else:
             if user and check_password_hash(user.password_hash, password):
                session['user_id'] = user.id
                return render_template('login.html', show_pin=True, email=email)
             else:
                flash('Invalid email or password.', 'error')
    
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('login.html', show_pin=True, email=user.email)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- CORE APP ROUTES ---
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'pin_verified' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/portfolio')
@login_required
def portfolio():
    user = User.query.get(session['user_id'])
    portfolio_data = get_portfolio_summary(user.id)
    return render_template('portfolio.html', portfolio=portfolio_data, funds=user.funds)

@app.route('/trade', methods=['GET', 'POST'])
@login_required
def trade():
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        if 'add_funds' in request.form:
            try:
                amount = Decimal(request.form.get('amount'))
                if amount > 0:
                    user.funds += amount
                    db.session.commit()
                    flash(f'₹{amount:.2f} added successfully.', 'success')
            except:
                flash('Invalid amount.', 'error')
        elif 'execute_trade' in request.form:
            symbol = request.form.get('symbol', '').upper().strip()
            try:
                quantity = int(request.form.get('quantity'))
                current_price = get_current_price(symbol)
                if current_price is None:
                    flash(f"Error: Could not find data for the stock symbol '{symbol}'. Please check the symbol and try again.", 'error')
                elif quantity <= 0:
                    flash('Quantity must be a positive number.', 'error')
                else:
                    total_cost = Decimal(quantity) * current_price
                    if user.funds < total_cost:
                        flash('Insufficient funds for this trade.', 'error')
                    else:
                        user.funds -= total_cost
                        new_trade = Trade(user_id=user.id, symbol=symbol, quantity=quantity, price=current_price, trade_type='buy')
                        db.session.add(new_trade)
                        db.session.commit()
                        flash(f'Successfully bought {quantity} shares of {symbol}.', 'success')
            except ValueError:
                flash('Invalid quantity. Please enter a whole number.', 'error')
            except Exception as e:
                flash(f'A system error occurred: {e}', 'error')
        elif 'execute_sell' in request.form:
            symbol = request.form.get('sell_symbol', '').upper().strip()
            try:
                quantity = int(request.form.get('sell_quantity'))
                if quantity <= 0:
                    flash('Quantity must be a positive number.', 'error')
                else:
                    # Get user's portfolio
                    portfolio = get_portfolio_summary(user.id)
                    if symbol not in portfolio:
                        flash(f"You do not own any shares of {symbol}.", 'error')
                    elif quantity > portfolio[symbol]['quantity']:
                        flash(f"You cannot sell more shares than you own. You have {portfolio[symbol]['quantity']} shares of {symbol} in your portfolio.", 'error')
                    else:
                        current_price = get_current_price(symbol)
                        if current_price is None:
                            flash(f"Error: Could not find data for the stock symbol '{symbol}'. Please check the symbol and try again.", 'error')
                        else:
                            # Credit funds and record the sale as a negative quantity
                            user.funds += Decimal(quantity) * current_price
                            new_trade = Trade(user_id=user.id, symbol=symbol, quantity=-quantity, price=current_price, trade_type='sell')
                            db.session.add(new_trade)
                            db.session.commit()
                            flash(f'Successfully sold {quantity} shares of {symbol} at ₹{current_price:.2f} each. ₹{(Decimal(quantity)*current_price):.2f} credited to your funds.', 'success')
            except ValueError:
                flash('Invalid quantity. Please enter a whole number.', 'error')
            except Exception as e:
                flash(f'A system error occurred: {e}', 'error')
    return render_template('trade.html', funds=user.funds)

# --- API FOR LIVE UPDATES ---
@app.route('/api/update-portfolio')
@login_required
def api_update_portfolio():
    portfolio = get_portfolio_summary(session['user_id'])
    symbols_to_fetch = [s + '.NS' for s in portfolio.keys()]
    if not symbols_to_fetch:
        return jsonify({})
    live_data = get_live_market_data(symbols_to_fetch)
    return jsonify(live_data)

# --- Main Execution ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)




