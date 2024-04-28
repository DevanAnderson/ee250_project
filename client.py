import requests

SERVER_URL = 'http://pi@172.20.10.3:5000'  #RPI

#handles login
def login(username, password):
    data = {'username': username, 'password': password}
    response = requests.post(f'{SERVER_URL}/login', json=data)
    return response.json(), response.status_code

#handles users portfolio
def get_portfolio(username):
    params = {'username': username}
    response = requests.get(f'{SERVER_URL}/portfolio', params=params)
    return response.json(), response.status_code

#handles trading stock, both buying and selling
def trade_stock(username, action, symbol, quantity):
    data = {'username': username, 'action': action, 'symbol': symbol, 'quantity': quantity}
    response = requests.post(f'{SERVER_URL}/trade', json=data)
    return response.json(), response.status_code

#handles depositing of cash
def deposit_cash(username, amount):
    data = {'username': username, 'amount': amount}
    response = requests.post(f'{SERVER_URL}/deposit', json=data)
    return response.json(), response.status_code

#handles withdrawing cash
def withdraw_cash(username, amount):
    data = {'username': username, 'amount': amount}
    response = requests.post(f'{SERVER_URL}/withdraw', json=data)
    return response.json(), response.status_code

#gets stock price of desired symbol
def view_stock_price(symbol):
    response = requests.get(f'{SERVER_URL}/stock_price?symbol={symbol}')
    return response.json()

#processes the resonse from the server and prints it in a more readable way
def process_and_print_response(response):
    if isinstance(response, dict):
        for key, value in response.items():
            print(f"{key.capitalize()}: {value}")
    else:
        print(response)

if __name__ == '__main__':
    try:
        username = input('Enter username: ')
        password = input('Enter password: ')

        # Login or create new user
        login_response, status_code = login(username, password)
        process_and_print_response(login_response)

        if status_code == 200:
            while True:
                print("\nOptions:")
                print("1. View Portfolio")
                print("2. View Price")
                print("3. Buy Stock")
                print("4. Sell Stock")
                print("5. Deposit Cash")
                print("6. Withdraw Cash")
                print("7. Exit")

                choice = input("Enter your choice (1-7): ")

                if choice == '1':
                    portfolio_response, _ = get_portfolio(username)
                    print("\nPortfolio:")
                    process_and_print_response(portfolio_response)
                elif choice == '2':
                    symbol = input("Enter stock symbol to view its price: ")
                    stock_price_response = view_stock_price(symbol)
                    process_and_print_response(stock_price_response)
                elif choice in ('3', '4'):
                    action = 'buy' if choice == '3' else 'sell'
                    symbol = input("Enter stock symbol: ")
                    quantity = int(input("Enter quantity: "))
                    trade_response, _ = trade_stock(username, action, symbol, quantity)
                    process_and_print_response(trade_response)
                elif choice == '5':
                    amount = float(input("Enter amount to deposit: "))
                    deposit_response, _ = deposit_cash(username, amount)
                    process_and_print_response(deposit_response)
                elif choice == '6':
                    amount = float(input("Enter amount to withdraw: "))
                    withdraw_response, _ = withdraw_cash(username, amount)
                    process_and_print_response(withdraw_response)
                elif choice == '7':
                    break
                else:
                    print("Invalid choice!")
    except KeyboardInterrupt:
        print("\Logging out")
