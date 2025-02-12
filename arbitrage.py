import public_markets
import observers
import config
import time
import logging
import json


class Arbitrer(object):
    def __init__(self):
        self.markets = []
        self.observers = []
        self.depths = {}
        self.init_markets(config.markets)
        self.init_observers(config.observers)

    def init_markets(self, markets):
        self.market_names = markets
        for market_name in markets:
            exec('import public_markets.' + market_name.lower())
            market = eval('public_markets.' + market_name.lower() + '.' + market_name + '()')
            self.markets.append(market)

    def init_observers(self, observers):
        self.observer_names = observers
        for observer_name in observers:
            exec('import observers.' + observer_name.lower())
            observer = eval('observers.' + observer_name.lower() + '.' + observer_name + '()')
            self.observers.append(observer)

    def get_profit_for(self, selling_index, buying_index, kask, kbid):
        # check to make sure input buying price actually lower than selling price
        if self.depths[kask]["asks"][selling_index]["price"] >= self.depths[kbid]["bids"][buying_index]["price"]:
            return 0, 0, 0, 0, 0

        # get the maximum amount of asks or bids that can current be filled by
        # the market within our spread
        max_amount_buy = 0
        for i in range(selling_index + 1):
            max_amount_buy += self.depths[kask]["asks"][i]["amount"]
        max_amount_sell = 0
        for j in range(buying_index + 1):
            max_amount_sell += self.depths[kbid]["bids"][j]["amount"]
        purchase_cap = float(config.max_purchase)
        # Determine an approximate maximum volume to buy by multiplying cofig value by lowest market price
        est_volume = purchase_cap / float(self.depths[kask]["asks"][i]["price"])
        max_amount = min(max_amount_buy, max_amount_sell, est_volume)

        buy_total = 0
        w_buyprice = 0
        total_available_volume = 0
        # For as long as we have bitcoin available, look for transactions we can make
        for i in range(selling_index + 1):
            price = self.depths[kask]["asks"][i]["price"]
            amount = min(max_amount, buy_total + self.depths[kask]["asks"][i]["amount"]) - buy_total
            total_available_volume += self.depths[kask]["asks"][i]["amount"]
            if amount <= 0:
                break
            buy_total += amount
            if w_buyprice == 0: # Set the buy price on the first run
                w_buyprice = price
            else:
                w_buyprice = (w_buyprice * (buy_total - amount) + price * amount) / buy_total
        sell_total = 0
        w_sellprice = 0
        for j in range(buying_index + 1):
            price = self.depths[kbid]["bids"][j]["price"]
            amount = min(max_amount, sell_total + self.depths[kbid]["bids"][j]["amount"]) - sell_total
            if amount < 0:
                break
            sell_total += amount
            if w_sellprice == 0:
                w_sellprice = price
            else:
                w_sellprice = (w_sellprice * (sell_total - amount) + price * amount) / sell_total

        profit = sell_total * w_sellprice - buy_total * w_buyprice
        return profit, sell_total, w_buyprice, w_sellprice, total_available_volume

    def get_max_depth(self, kask, kbid):
        i = 0
        if len(self.depths[kbid]["bids"]) != 0 and len(self.depths[kask]["asks"]) != 0:
            # Create a list of the indices of selling offer key/pairs (price, volume) that are less than the current max buying offer
            while self.depths[kask]["asks"][i]["price"] < self.depths[kbid]["bids"][0]["price"]:
                if i >= len(self.depths[kask]["asks"]) - 1:
                    break
                i += 1
        j = 0
        if len(self.depths[kask]["asks"]) != 0 and len(self.depths[kbid]["bids"]) != 0:
            # Create a list of the indices of buying offer key/pairs that are less than the current maxium selling offer
            while self.depths[kask]["asks"][0]["price"] < self.depths[kbid]["bids"][j]["price"]:
                if j >= len(self.depths[kbid]["bids"]) - 1:
                    break
                j += 1
        max_selling_index = i
        max_buying_index = j
        return max_selling_index, max_buying_index

    def arbitrage_depth_opportunity(self, kask, kbid):
        # Get the maximum index of the overlap
        max_selling_indices, max_buying_indices = self.get_max_depth(kask, kbid)
        best_profit = 0
        best_selling_index, best_buying_index = (0, 0)
        best_w_buyprice, best_w_sellprice = (0, 0)
        best_volume = 0
        for selling_index in range(max_selling_indices + 1):
            for buying_index in range(max_buying_indices + 1):
                profit, volume, w_buyprice, w_sellprice, total_available_volume = self.get_profit_for(selling_index, buying_index, kask, kbid)
                if profit >= 0 and profit >= best_profit:
                    best_profit = profit
                    best_volume = volume
                    best_w_buyprice, best_w_sellprice = (w_buyprice, w_sellprice)
                    best_selling_index, best_buying_index = (selling_index, buying_index)
                    available_volume = total_available_volume
        # Account for transaction fees
        buying_fees = self.fees[kask]
        selling_fees = self.fees[kbid]
        fee_adjusted_volume = (1 - float(buying_fees['exchange_rate'])) * best_volume # Volume2*adjusted volume; Volume1*original volume
        sale_total = fee_adjusted_volume * best_w_sellprice 
        buy_total = best_volume * best_w_buyprice
        # Fix divide by 0 error
        if buy_total == 0:
            return 0, 0, 0, 0, 0, 0, 0, 0
        tx_fee_discount = 1 - float(selling_fees['exchange_rate'])
        percent_profit = ((sale_total * tx_fee_discount) / buy_total - 1) * 100
        fee_adjusted_profit = (sale_total * tx_fee_discount) - buy_total
        return fee_adjusted_profit, fee_adjusted_volume, percent_profit, self.depths[kask]["asks"][best_selling_index]["price"],\
            self.depths[kbid]["bids"][best_buying_index]["price"], best_w_buyprice, best_w_sellprice, available_volume

    def arbitrage_opportunity(self, kask, ask, kbid, bid):
        # perc = (bid["price"] - ask["price"]) / bid["price"] * 100
        profit, purchase_volume, percent_profit, buyprice, sellprice, weighted_buyprice,\
            weighted_sellprice, available_volume = self.arbitrage_depth_opportunity(kask, kbid)
        if purchase_volume == 0 or buyprice == 0:
            return
        # maxme_percent_profit is original calculation however it seems off so a simpler one replaces it in arbitrage_depth_opportunity
        # maxme_percent_profit = (1 - (volume - (profit / weighted_buyprice)) / volume) * 100
        
        if percent_profit < float(config.perc_thresh):
            return
        for observer in self.observers:
            observer.opportunity(profit, purchase_volume, buyprice, kask, sellprice, kbid,
                                 percent_profit, weighted_buyprice, weighted_sellprice, available_volume, config.max_purchase)

    def update_depths(self):
        depths = {}
        fees = {}
        for market in self.markets:
            depths[market.name] = market.get_depth()
            fees[market.name] = market.fees
        return depths, fees

    def tickers(self):
        for market in self.markets:
            try:
                logging.debug("ticker: " + market.name + " - " + str(market.get_ticker()))
            except:
                logging.debug("error: unable to get ticker for " + market.name)

    def replay_history(self, directory):
        import os
        import json
        import pprint
        files = os.listdir(directory)
        files.sort()
        for f in files:
            depths = json.load(open(directory + '/' + f, 'r'))
            self.depths = {}
            for market in self.market_names:
                if market in depths:
                    self.depths[market] = depths[market]
            self.tick()

    def tick(self):
        for observer in self.observers:
            observer.begin_opportunity_finder(self.depths)

        for kmarket1 in self.depths:
            for kmarket2 in self.depths:
                if kmarket1 == kmarket2:  # same market
                    continue
                market1 = self.depths[kmarket1]
                market2 = self.depths[kmarket2]
                # spammy debug command for testing if there is market liquidity
                # print "Is " + kmarket1 + " at " + str(market1["asks"][0]['price']) + " less than " + kmarket2 + " at " + str(market2["bids"][0]['price']) + "?"
                if float(market1["asks"][0]['price']) < float(market2["bids"][0]['price']):
                    self.arbitrage_opportunity(kmarket1, market1["asks"][0], kmarket2, market2["bids"][0])

        for observer in self.observers:
            observer.end_opportunity_finder()

    def loop(self):
        while True:
            self.depths, self.fees = self.update_depths()
            self.tickers()
            self.tick()
            time.sleep(20)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="more verbose", action="store_true")
    parser.add_argument("-r", "--replay-history", type=str, help="replay history from a directory")
    parser.add_argument("-o", "--observers", type=str, help="observers")
    parser.add_argument("-m", "--markets", type=str, help="markets")
    args = parser.parse_args()
    level = logging.INFO
    if args.verbose:
        level = logging.DEBUG
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=level)
    arbitrer = Arbitrer()
    if args.replay_history:
        if args.observers:
            arbitrer.init_observers(args.observers.split(","))
        if args.markets:
            arbitrer.init_markets(args.markets.split(","))
        arbitrer.replay_history(args.replay_history)
    else:
        arbitrer.loop()

if __name__ == '__main__':
    main()
