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
        if stock.price is None or np.isnan(stock.price):
            return 0  # Prevent NaN prices from being used
        return (stock.price * (1 - stock.risk) + self.stock_valuations[stock.name] * stock.risk) / (1 + stock.risk)

    def list_shares_for_sale(self):
        orders = []
        for stock_name, quantity in self.portfolio.items():
            if quantity > 0:
                stock = StockMarket.get_stock(stock_name)
                ask_price = self.evaluate_stock(stock)
                if not np.isnan(ask_price) and ask_price > 0:
                    orders.append(('sell', stock_name, quantity, ask_price))
        return orders

    def place_bid(self):
        stock = random.choice(list(StockMarket.stocks.values()))
        bid_price = self.evaluate_stock(stock)
        if np.isnan(bid_price) or bid_price <= 0:
            return None  # Skip placing a bid if price is invalid
        quantity_to_buy = int(self.cash // stock.price) if self.cash >= stock.price and not np.isnan(stock.price) else 0
        if quantity_to_buy > 0:
            return ('buy', stock.name, quantity_to_buy, bid_price)
        return None

    def execute_trade(self, order_type, stock_name, quantity, price):
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
            if stock and not np.isnan(stock.price):
                self.portfolio_value += stock.price * quantity

        if self.portfolio_age > 0:
            self.risk_tolerance = (self.risk_tolerance * self.portfolio_age + (self.portfolio_value - self.cash) * 0.1) / (self.portfolio_age + 1)

        self.portfolio_age += 1

    def make_decision(self, stock):
        # Show the stock price history
        plt.plot(stock.history)
        plt.title(f'Stock Price History for {stock.name}')
        plt.xlabel('Time')
        plt.ylabel('Price')
        plt.show()

        # User input for buy/hold/sell decision
        decision = input(f"Do you want to buy, hold, or sell {stock.name}? (Enter 'buy', 'hold', 'sell'): ").lower()
        if decision == 'buy':
            amount_to_buy = int(input(f"How many shares of {stock.name} do you want to buy? "))
            return ('buy', stock.name, amount_to_buy, stock.price)
        elif decision == 'sell':
            amount_to_sell = int(input(f"How many shares of {stock.name} do you want to sell? "))
            return ('sell', stock.name, amount_to_sell, stock.price)
        else:
            return None

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
        total_volume = 0
        trade_prices = []

        buy_orders.sort(key=lambda x: -x[3])
        sell_orders.sort(key=lambda x: x[3])

        while buy_orders and sell_orders:
            buy_order = buy_orders[0]
            sell_order = sell_orders[0]

            if buy_order[3] >= sell_order[3]:
                trade_price = (buy_order[3] + sell_order[3]) / 2
                quantity = min(buy_order[2], sell_order[2])

                trade_prices.append((trade_price, quantity))
                total_volume += quantity

                buy_order[2] -= quantity
                sell_order[2] -= quantity

                if buy_order[2] == 0:
                    buy_orders.pop(0)
                if sell_order[2] == 0:
                    sell_orders.pop(0)
            else:
                break

        if trade_prices:
            volume_weighted_price = sum(price * vol for price, vol in trade_prices) / total_volume
            self.price = volume_weighted_price if not np.isnan(volume_weighted_price) else self.price
            self.last_trade_price = self.price
        else:
            self.price = self.price * (1 + random.uniform(-0.01, 0.01)) if not np.isnan(self.price) else self.last_trade_price

        self.history.append(self.price)

class StockMarket:
    stocks = {}

    @classmethod
    def add_stock(cls, stock):
        cls.stocks[stock.name] = stock

    @classmethod
    def get_stock(cls, stock_name):
        return cls.stocks.get(stock_name)

    @classmethod
    def simulate_trading_day(cls, traders):
        buy_orders = []
        sell_orders = []

        for trader in traders:
            bid_order = trader.place_bid()
            if bid_order:
                buy_orders.append(bid_order)

            sell_orders.extend(trader.list_shares_for_sale())

        for stock in cls.stocks.values():
            stock.update_price(buy_orders, sell_orders)

        # Allow user to make decisions on their stocks
        player = traders[0]  # Assume the first trader is the user
        for stock_name in player.portfolio:
            stock = cls.get_stock(stock_name)
            if stock:
                decision = player.make_decision(stock)
                if decision:
                    player.execute_trade(*decision)

    @classmethod
    def simulate_year(cls, traders, days=365):
        for _ in range(days):
            cls.simulate_trading_day(traders)
