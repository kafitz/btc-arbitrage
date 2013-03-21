import urllib2
import json
import logging
from market import Market


class MtGoxUSD(Market):
    def __init__(self):
        super(MtGoxUSD, self).__init__("USD")
        self.update_rate = 25

    def update_depth(self):
        res = urllib2.urlopen('http://data.mtgox.com/api/1/BTCUSD/depth/fetch')
        jsonstr = res.read()
        try:
	        depth = json.loads(jsonstr)
	        self.depth = self.format_depth(depth)
        except Exception:
            logging.warn("Can't parse json:" + jsonstr)

    def sort_and_format(self, l, reverse=False):
    	ret = []
    	for i in l:
    		ret.append({'price': i.get('price'), 'amount': i.get('amount')})
    	return ret


    def format_depth(self, depth):
        bids = self.sort_and_format(depth['return']['bids'])
        asks = self.sort_and_format(depth['return']['asks'])
        return {'asks': asks, 'bids': bids}

if __name__ == "__main__":
    market = MtGoxUSD()
    print market.get_depth()