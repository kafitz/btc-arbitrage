from market import Market
import time
import urllib
import urllib2
import sys
import json
sys.path.append('../')
sys.path.append('.')
import config


class PrivateBitstamp(Market):
    ticker_url = {"method": "GET", "url": "https://www.bitstamp.net/api/ticker/"}
    buy_url = {"method": "POST", "url": "https://www.bitstamp.net/api/buy/"}
    sell_url = {"method": "POST", "url": "https://www.bitstamp.net/api/sell/"}
    order_url = {"method": "GET", "url": "https://www.bitstamp.net/api/user_transactions/"}
    open_orders_url = {"method": "POST", "url": "https://www.bitstamp.net/api/open_orders/"}
    info_url = {"method": "POST", "url": "https://www.bitstamp.net/api/balance/"}

    def __init__(self):
        super(Market, self).__init__()
        self.user = config.bitstamp_user
        self.password = config.bitstamp_password
        self.currency = "USD"
        #self.get_info()

    def _send_request(self, url, params, extra_headers=None):
        headers = {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        }
        if extra_headers is not None:
            for k, v in extra_headers.iteritems():
                headers[k] = v
        
        req = urllib2.Request(url['url'], urllib.urlencode(params), headers)
        response = urllib2.urlopen(req)
        if response.getcode() == 200:
            jsonstr = response.read()
            return json.loads(jsonstr)
        return None

    def trade(self, amount, url, price):
        # Next line is commented out to avoid accidental trades, use with caution
        #params = {"user": self.user, "password": self.password, "amount": str(self.amount), "price": str(self.price)}
        response = self._send_request(self.url, params)
        print response
        if response and "result" in response and response["result"] == "success":
            return response["return"]
        return None

    def buy(self, amount, price):
        return self.trade(amount, buy_url, price)

    def sell(self, amount, price):
        return self.trade(amount, sell_url, price)

    def get_info(self):
        params = {"user": self.user, "password": self.password}
        response = self._send_request(self.info_url, params)

        if response and "error" not in response:
            self.usd_balance = float(response["usd_balance"])
            self.btc_balance = float(response["btc_balance"])
            self.usd_reserved = float(response["usd_reserved"])
            self.btc_reserved = float(response["btc_reserved"])
            self.usd_available = float(response["usd_available"])
            self.btc_available = float(response["btc_balance"])
            self.fee = float(response["fee"])
            return 1
        else:
            self.error = str(response["error"])
            print self.error
            return 1
        return None

    def __str__(self):
        return str({"usd_balance": self.usd_balance, "btc_balance": self.btc_balance, "usd_reserved": self.usd_reserved, "btc_reserved": self.btc_reserved, "usd_available": self.usd_available, "btc_available": self.btc_available, "fee": self.fee})


if __name__ == "__main__":
    bitstamp = PrivateBitstamp()
    bitstamp.get_info()
    print bitstamp
