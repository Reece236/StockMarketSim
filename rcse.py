'''
Welcome to the Reece Calvin Stock Exechange (RCSE)! We are open from 10:00 AM to 6:00 PM, Monday through Friday.
We are closed on all jewish holidays and arbor day.
'''
import random
from datetime import datetime, timedelta
from matplotlib import pyplot as plt
import numpy as np

class Trader:
    def __init__(self, name, cash):
        self.name = name
        self.cash = cash
        self.portfolio = {}
        self.risk_tolerance = random.uniform(0, 1)
        self.stock_valuations = {}
        self.options_portfolio = {}
        self.portfolio_value = 0
        self.portfolio_age = 0

    def __str__(self):
        return f'{self.name} has ${self.cash:.2f} in cash and owns {self.portfolio}.'

    def set_stock_valuations(self, stocks):
        for stock in stocks.values():
            delta_value = np.random.binomial(100, 0.5) / 100
            stock_valuation = delta_value * stock.risk
            self.stock_valuations[stock.name] = stock_valuation

    def evaluate_stock(self, stock):
        return (stock.price * (1 - stock.risk) + self.stock_valuations[stock.name] * stock.risk) / (1 + stock.risk)

    def list_shares_for_sale(self):
        '''
        List all shares owned by the trader for sale at their personal valuation.
        '''
        orders = []
        for stock_name, quantity in self.portfolio.items():
            if quantity > 0:
                stock = StockMarket.get_stock(stock_name)
                ask_price = self.evaluate_stock(stock)
                orders.append(('sell', stock_name, quantity, ask_price))
        return orders

    def place_bid(self):
        '''
        Randomly place a bid for a stock.
        '''
        stock = random.choice(list(StockMarket.stocks.values()))
        bid_price = self.evaluate_stock(stock)
        quantity_to_buy = int(self.cash // stock.price) if self.cash >= stock.price else 0
        if quantity_to_buy > 0:
            return ('buy', stock.name, quantity_to_buy, bid_price)
        return None

    def execute_trade(self, order_type, stock_name, quantity, price):
        '''
        Execute a trade, updating portfolio and cash.
        '''
        stock = StockMarket.get_stock(stock_name)
        if order_type == 'buy':
            total_cost = price * quantity
            if self.cash >= total_cost:
                self.cash -= total_cost
                self.portfolio[stock_name] = self.portfolio.get(stock_name, 0) + quantity
                stock.quantity -= quantity
        elif order_type == 'sell':
            if self.portfolio.get(stock_name, 0) >= quantity:
                total_revenue = price * quantity
                self.cash += total_revenue
                self.portfolio[stock_name] -= quantity
                stock.quantity += quantity
                if self.portfolio[stock_name] == 0:
                    del self.portfolio[stock_name]

    def update_portfolio(self):
        self.portfolio_value = 0
        for stock_name, quantity in self.portfolio.items():
            stock = StockMarket.get_stock(stock_name)
            if stock:
                self.portfolio_value += stock.price * quantity

        if self.portfolio_age > 0:
            self.risk_tolerance = (self.risk_tolerance * self.portfolio_age + (self.portfolio_value - self.cash) * 0.1) / (self.portfolio_age + 1)

        self.portfolio_age += 1

class Stock:
    def __init__(self, name, price, quantity, sector, risk):
        self.name = name
        self.price = price
        self.quantity = quantity
        self.sector = sector
        self.risk = risk
        self.outstanding_shares = quantity
        self.history = [price]
        self.last_trade_price = price

    def __str__(self):
        return f'{self.name} is priced at ${self.price:.2f}.'

    def update_price(self, buy_orders, sell_orders):
        """
        Update the stock price based on the matched orders.
        """
        total_volume = 0
        trade_prices = []

        # Sort buy orders by price descending, sell orders by price ascending
        buy_orders.sort(key=lambda x: -x[3])
        sell_orders.sort(key=lambda x: x[3])

        while buy_orders and sell_orders:
            buy_order = buy_orders[0]
            sell_order = sell_orders[0]

            # If buy price is greater than or equal to sell price, execute trade
            if buy_order[3] >= sell_order[3]:
                trade_price = (buy_order[3] + sell_order[3]) / 2
                quantity = min(buy_order[2], sell_order[2])

                # Track the trade prices and volumes
                trade_prices.append((trade_price, quantity))
                total_volume += quantity

                # Update the orders after trade execution
                buy_order[2] -= quantity
                sell_order[2] -= quantity

                if buy_order[2] == 0:
                    buy_orders.pop(0)
                if sell_order[2] == 0:
                    sell_orders.pop(0)

            else:
                break

        # Determine new price based on the volume-weighted average of trade prices
        if trade_prices:
            volume_weighted_price = sum(price * vol for price, vol in trade_prices) / total_volume
            self.price = volume_weighted_price
            self.last_trade_price = volume_weighted_price
        else:
            # No trades occurred, adjust price slightly towards last trade price
            self.price = self.price * (1 + random.uniform(-0.01, 0.01))

        self.history.append(self.price)


class Option:
    def __init__(self, option_type, stock, strike_price, expiry_date):
        self.option_type = option_type  # 'call' or 'put'
        self.stock = stock
        self.strike_price = strike_price
        self.expiry_date = expiry_date
        self.price = self.calculate_price()

    def calculate_price(self):
        # Simplified pricing based on Black-Scholes formula approximation
        time_to_expiry = (self.expiry_date - datetime.now()).days / 365
        volatility = random.uniform(0.1, 0.5)
        intrinsic_value = max(0, self.stock.price - self.strike_price) if self.option_type == 'call' else max(0, self.strike_price - self.stock.price)
        time_value = volatility * self.stock.price * time_to_expiry
        return intrinsic_value + time_value

    def __str__(self):
        return f'{self.option_type.capitalize()} Option for {self.stock.name} at ${self.strike_price} expiring on {self.expiry_date} is priced at ${self.price:.2f}.'

class StockMarket:
    market_open = False
    stocks = {}
    order_book = {'buy': [], 'sell': []}

    @staticmethod
    def match_orders():
        """
        Match buy and sell orders from the order book.
        """
        # Reset each stock's order book
        stock_order_books = {stock.name: {'buy': [], 'sell': []} for stock in StockMarket.stocks.values()}

        # Distribute orders into individual stock order books
        for buy_order in StockMarket.order_book['buy']:
            stock_order_books[buy_order[1]]['buy'].append(buy_order)

        for sell_order in StockMarket.order_book['sell']:
            stock_order_books[sell_order[1]]['sell'].append(sell_order)

        # Process each stock's order book
        for stock_name, orders in stock_order_books.items():
            stock = StockMarket.get_stock(stock_name)
            if stock:
                stock.update_price(orders['buy'], orders['sell'])

    @staticmethod
    def simulate_trading_day(traders):
        if not StockMarket.market_open:
            print("Market is closed, cannot simulate trading.")
            return

        StockMarket.order_book = {'buy': [], 'sell': []}

        for trader in traders:
            sell_orders = trader.list_shares_for_sale()
            for order in sell_orders:
                StockMarket.order_book['sell'].append((trader, *order))

            bid_order = trader.place_bid()
            if bid_order:
                StockMarket.order_book['buy'].append((trader, *bid_order))

        StockMarket.match_orders()

    @staticmethod
    def simulate_year(traders, days=252):
        for _ in range(days):
            StockMarket.simulate_trading_day(traders)

def plot_stock_trends(stocks):
    """
    Plots the trend of each stock's price over the simulation period.
    """
    plt.figure(figsize=(14, 8))
    for stock in stocks.values():
        plt.plot(stock.history, label=stock.name)
    plt.title('Stock Price Trends Over the Year')
    plt.xlabel('Days')
    plt.ylabel('Price')
    plt.yscale('log')
    plt.legend(loc='upper left', fontsize='small')
    plt.show()

def plot_wealth_disparity(traders):
    """
    Plots the distribution of wealth among traders at the end of the simulation.
    """
    wealth = [trader.cash + trader.portfolio_value for trader in traders]
    plt.figure(figsize=(10, 6))
    plt.hist(wealth, bins=50, color='skyblue', edgecolor='black')
    plt.title('Wealth Disparity Among Traders')
    plt.xlabel('Total Wealth (Cash + Portfolio Value)')
    plt.ylabel('Number of Traders')
    plt.show()

def plot_sector_performance(stocks):
    """
    Plots the aggregated performance trends for different sectors.
    """
    sector_performance = {}
    for stock in stocks.values():
        if stock.sector not in sector_performance:
            sector_performance[stock.sector] = np.array(stock.history)
        else:
            sector_performance[stock.sector] += np.array(stock.history)

    plt.figure(figsize=(12, 6))
    for sector, history in sector_performance.items():
        plt.plot(history / len([s for s in stocks.values() if s.sector == sector]), label=sector)
    plt.title('Sector Performance Trends Over the Year')
    plt.xlabel('Days')
    plt.ylabel('Average Price')
    plt.yscale('log')
    plt.legend(loc='upper left')
    plt.show()

def plot_options_activity(options):
    """
    Plots the trends in options prices over the simulation period.
    """
    call_prices, put_prices, days = [], [], []
    for option in options:
        if option.option_type == 'call':
            call_prices.append(option.price)
        else:
            put_prices.append(option.price)
        days.append(option.expiry_date)

    plt.figure(figsize=(12, 6))
    plt.plot(days, call_prices, label='Call Options', marker='o')
    plt.plot(days, put_prices, label='Put Options', marker='o')
    plt.title('Options Trading Activity Over the Year')
    plt.xlabel('Days')
    plt.ylabel('Option Price')
    plt.legend(loc='upper left')
    plt.show()

def plot_risk_return(traders):
    """
    Plots the risk tolerance of traders against their final portfolio value.
    """
    risk = [trader.risk_tolerance for trader in traders]
    wealth = [trader.cash + trader.portfolio_value for trader in traders]

    plt.figure(figsize=(10, 6))
    plt.scatter(risk, wealth, c='blue', alpha=0.5)
    plt.title('Risk Tolerance vs. Wealth')
    plt.xlabel('Risk Tolerance')
    plt.ylabel('Total Wealth (Cash + Portfolio Value)')
    plt.show()

# Initialize market and stocks
sectors = ['Tech', 'Health', 'Finance', 'Energy', 'Retail']
for i in range(100):
    name = f'Stock_{i+1}'
    price = np.random.lognormal(.72, 1.08) * 75
    quantity = random.randint(1000, 10000)
    sector = random.choice(sectors)
    risk = random.uniform(0.1, 0.9)
    stock = Stock(name, price, quantity, sector, risk)
    StockMarket.add_stock(stock)

# Initialize traders
traders = [Trader(f'Trader_{i+1}', random.uniform(10000, 500000)) for i in range(2000)]

for trader in traders:
    trader.set_stock_valuations(StockMarket.stocks)

# Open market and simulate trading for a year
StockMarket.open_market()
StockMarket.simulate_year(traders)
StockMarket.close_market()

plot_stock_trends(StockMarket.stocks)
plot_wealth_disparity(traders)
plot_sector_performance(StockMarket.stocks)
plot_risk_return(traders)
