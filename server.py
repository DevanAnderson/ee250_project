import sys
sys.path.append('~/Dexter/GrovePi/Software/Python')
from flask import Flask, request, jsonify
import json
import os
import yfinance as yf
import threading
import random
import time
import grovepi
from grove_rgb_lcd import *

app = Flask(__name__)

USERS_FILE = 'users.json'

LCD_COLS = 16  # Number of columns in the LCD
LCD_ROWS = 2  # Number of rows in the LCD

def display_on_lcd(text):
    setText("") #clear the screen
    setText_norefresh(text)  # Update LCD text without refreshing the screen
    setRGB(0, 255,0)

def fetch_random_symbol_price():
    all_symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'FB', 'TSLA', 'NFLX', 'NVDA', 'PYPL', 'INTC',
                  'BABA', 'JD', 'TSM', 'NVTA', 'ZM', 'CRM', 'DIS', 'NKE', 'KO', 'PEP',
                  'BA', 'CSCO', 'IBM', 'ORCL', 'ADBE', 'UBER', 'LYFT', 'WMT', 'HD', 'LOW',
                  'COST', 'MCD', 'SBUX', 'JNJ', 'PFE', 'MRNA', 'JPM', 'BAC', 'GS', 'MS',
                  'WFC', 'V', 'MA', 'PYPL', 'SQ', 'AMT', 'CCI', 'SBAC', 'T', 'VZ',
                  'CVS', 'AAL', 'DAL', 'UAL', 'LUV', 'CCL', 'RCL', 'CMG', 'YUM', 'DPZ',
                  'AAP', 'UBER', 'LYFT', 'EBAY', 'SHOP', 'TWTR', 'SNAP', 'ROKU', 'PTON', 'FSLY',
                  'ATVI', 'EA', 'TTWO', 'DISCA', 'FOXA', 'CMCSA', 'VIAC', 'NFLX', 'AMCX', 'ROKU',
                  'XOM', 'CVX', 'BP', 'TOT', 'COP', 'APC', 'OXY', 'HAL', 'SLB',
                  'CAT', 'DE', 'MMM', 'JCI', 'EMR', 'HON', 'GE', 'ITW', 'WM', 'RSG',
                  'NEM', 'GOLD', 'ABX', 'AEM', 'FNV', 'WPM', 'RGLD', 'KL', 'AG', 'PAAS'] #some popular symbols to display on the LCD
    while True:
        try:
            random_symbol = random.choice(all_symbols)
            stock = yf.Ticker(random_symbol)
            current_price = stock.history(period='1d').iloc[-1]['Close']
            display_text = f"{random_symbol}: \n${current_price}"  # Text to display on LCD
            print(display_text)  # Print for debugging
            display_on_lcd(display_text)  # Display on LCD
        except Exception as e:
            print(f"Failed to fetch price for {random_symbol}: {str(e)}")
        time.sleep(15)

fetch_thread = threading.Thread(target=fetch_random_symbol_price)
fetch_thread.daemon = True  # Daemonize the thread so it stops with the main thread
fetch_thread.start()  # Start the fetch thread

# Initialize data if files don't exist
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

# Load data from files
with open(USERS_FILE, 'r') as f:
    users = json.load(f)

def save_users():
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def calculate_net_worth(portfolio):
    net_worth = portfolio.get('cash', 0)  # Start with the cash balance

    for symbol, quantity in portfolio.items():
        if symbol != 'cash':  # Skip the 'cash' key
            stock = yf.Ticker(symbol)
            historical_data = stock.history(period='1d')
            if not historical_data.empty:
                latest_price = historical_data.iloc[-1]['Close']
                stock_value = quantity * latest_price
                net_worth += stock_value

    return net_worth


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username in users and users[username]['password'] == password:
        return jsonify({'message': 'Login successful!'}), 200
    else:
        # Create a new user if the username is not found
        if username not in users:
            users[username] = {'password': password, 'portfolio': {'cash': 0}}
            save_users()
            return jsonify({'message': 'New user created and logged in!'}), 200
        else:
            return jsonify({'error': 'Invalid credentials!'}), 401

@app.route('/stock', methods=['GET'])
def get_stock_data():
    symbol = request.args.get('symbol')

    if symbol:
        stock = yf.Ticker(symbol)
        info = stock.info
        return jsonify(info), 200
    else:
        return jsonify({'error': 'Invalid symbol!'}), 400

@app.route('/trade', methods=['POST'])
@app.route('/trade', methods=['POST'])
def trade_stock():
    data = request.json
    username = data.get('username')
    action = data.get('action')
    symbol = data.get('symbol')
    quantity = data.get('quantity')

    if not (username and action and symbol and quantity is not None):
        return jsonify({'error': 'Missing required parameters!'}), 400

    if action not in ['buy', 'sell']:
        return jsonify({'error': 'Invalid action!'}), 400

    if username not in users:
        return jsonify({'error': 'User not found!'}), 404

    try:
        stock = yf.Ticker(symbol)
        historical_data = stock.history(period='1d')
        if historical_data.empty:
            return jsonify({'error': 'Symbol not found!'}), 400
        price_per_stock = historical_data.iloc[-1]['Close']
    except ValueError:
        return jsonify({'error': 'Invalid symbol format!'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve data: {str(e)}'}), 500

    if action == 'buy':
        if 'cash' not in users[username]['portfolio']:
            users[username]['portfolio']['cash'] = 0

        cost = quantity * price_per_stock

        if cost > users[username]['portfolio']['cash']:
            return jsonify({'error': 'Insufficient funds!'}), 400

        users[username]['portfolio']['cash'] -= cost
        users[username]['portfolio'][symbol] = users[username]['portfolio'].get(symbol, 0) + quantity
        save_users()
        return jsonify({'message': f'Stock bought successfully! Price per stock: ${price_per_stock}'}), 200
    elif action == 'sell':
        if symbol not in users[username]['portfolio'] or users[username]['portfolio'][symbol] < quantity:
            return jsonify({'error': 'Insufficient stock or invalid symbol!'}), 400

        earnings = quantity * price_per_stock
        users[username]['portfolio']['cash'] += earnings
        users[username]['portfolio'][symbol] -= quantity

        if users[username]['portfolio'][symbol] == 0:
            del users[username]['portfolio'][symbol]  # Remove stock if quantity becomes zero

        save_users()
        return jsonify({'message': f'Stock sold successfully! Price per stock: ${price_per_stock}'}), 200



@app.route('/deposit', methods=['POST'])
def deposit_cash():
    data = request.json
    username = data.get('username')
    amount = data.get('amount')

    if username in users and amount > 0:
        users[username]['portfolio']['cash'] += amount
        save_users()
        return jsonify({'message': 'Cash deposited successfully!'}), 200
    else:
        return jsonify({'error': 'Invalid deposit!'}), 400

@app.route('/withdraw', methods=['POST'])
def withdraw_cash():
    data = request.json
    username = data.get('username')
    amount = data.get('amount')

    if username in users and amount > 0 and amount <= users[username]['portfolio']['cash']:
        users[username]['portfolio']['cash'] -= amount
        save_users()
        return jsonify({'message': 'Cash withdrawn successfully!'}), 200
    else:
        return jsonify({'error': 'Invalid withdrawal amount or insufficient funds!'}), 400

@app.route('/portfolio', methods=['GET'])
def get_portfolio():
    username = request.args.get('username')

    if username in users:
        portfolio = users[username]['portfolio']
        # Create a copy of the portfolio to avoid modifying the original
        portfolio_copy = portfolio.copy()
        net_worth = calculate_net_worth(portfolio)
        portfolio_copy['net worth'] = calculate_net_worth(portfolio)
        return jsonify(portfolio_copy), 200
    else:
        return jsonify({'error': 'User not found!'}), 404

@app.route('/stock_price', methods=['GET'])
def get_stock_price():
    symbol = request.args.get('symbol')

    if not symbol:
        return jsonify({'error': 'Symbol parameter is missing!'}), 400

    try:
        stock = yf.Ticker(symbol)
        historical_data = stock.history(period='1d')
        if historical_data.empty:
            return jsonify({'error': 'No historical data found for the symbol!'}), 400
        current_price = historical_data.iloc[-1]['Close']
        return jsonify({'symbol': symbol, 'price': current_price}), 200
    except ValueError:
        return jsonify({'error': 'Invalid symbol format!'}), 400
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve data: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
