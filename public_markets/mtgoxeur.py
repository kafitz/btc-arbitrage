import urllib2
import json
import logging
from market import Market


class MtGoxEUR(Market):
    def __init__(self):
        super(MtGoxEUR, self).__init__("EUR")
        self.update_rate = 25

    def update_depth(self):
        res = urllib2.urlopen('http://data.mtgox.com/api/1/BTCEUR/depth/fetch')
        jsonstr = res.read()
        try:
            depth = json.loads(jsonstr)
            self.depth = self.format_depth(depth)
        except Exception:
            logging.warn("Can't parse json:" + jsonstr)

    def sort_and_format(self, l, reverse=False):
        # sort list: for each dict in input list, get price key and sort by that
        l.sort(key=lambda x: float(x.get('price')), reverse=reverse)
        ret = []
        for i in l:
            # create a return a list of dicts sorted according to bid/ask w/ only the price and volume
            ret.append({'price': float(i.get('price')), 'amount': float(i.get('amount'))})
        return ret

    def format_depth(self, depth):
        # returns a dict for comparison against other exchanges in arbitrage.py:tick()
        bids = self.sort_and_format(depth['return']['bids'], True)
        asks = self.sort_and_format(depth['return']['asks'], False)
        return {'asks': asks, 'bids': bids}

if __name__ == "__main__":
    market = MtGoxEUR()
    print market.get_depth()
