from market import Market
import time
import base64
import hmac
import urllib
import urllib2
import hashlib
import sys
import json
sys.path.append('../')
sys.path.append('.')
import config
import re
from decimal import Decimal


class PrivateBitstamp(Market):
    ticker_url = {"method": "GET", "url": "https://www.bitstamp.net/api/ticker/"}
    buy_url = {"method": "POST", "url": "https://www.bitstamp.net/api/buy/"}
    sell_url = {"method": "POST", "url": "https://www.bitstamp.net/api/sell/"}
    order_url = {"method": "GET", "url": "https://www.bitstamp.net/api/user_transactions/"}
    open_orders_url = {"method": "POST", "url": "https://www.bitstamp.net/api/open_orders/"}
    info_url = {"method": "POST", "url": "https://www.bitstamp.net/api/balance/"}

    def __init__(self):
        super(Market, self).__init__()
        self.key = config.bitstamp_key
        self.secret = config.bitstamp_secret
        self.currency = "USD"
        self.get_info()

    def _create_nonce(self):
        return int(time.time() * 1000000)

    def _change_currency_url(self, url, currency):
        return re.sub(r'BTC\w{3}', r'BTC' + currency, url)

    def _to_int_price(self, price, currency):
        ret_price = None
        if currency in ["USD", "EUR", "GBP", "PLN", "CAD", "AUD", "CHF", "CNY",
                        "NZD", "RUB", "DKK", "HKD", "SGD", "THB"]:
            ret_price = Decimal(price)
            ret_price = int(price * 100000)
        elif currency in ["JPY", "SEK"]:
            ret_price = Decimal(price)
            ret_price = int(price * 1000)
        return ret_price

    def _to_int_amount(self, amount):
        amount = Decimal(amount)
        return int(amount * 100000000)

    def _from_int_amount(self, amount):
        return Decimal(amount) / Decimal(100000000.)

    def _from_int_price(self, amount):
        # FIXME: should take JPY and SEK into account
        return Decimal(amount) / Decimal(100000.)

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

    def trade(self, amount, ttype, price=None):
        if price:
            price = self._to_int_price(price, self.currency)
        amount = self._to_int_amount(amount)

        self.buy_url["url"] = self._change_currency_url(self.buy_url["url"], self.currency)

        params = [("nonce", self._create_nonce()),
                  ("amount_int", str(amount)),
                  ("type", ttype)]
        if price:
            params.append(("price_int", str(price)))

        response = self._send_request(self.buy_url, params)
        if response and "result" in response and response["result"] == "success":
            return response["return"]
        return None

    def buy(self, amount, price=None):
        return self.trade(amount, "bid", price)

    def sell(self, amount, price=None):
        return self.trade(amount, "ask", price)

    def get_info(self):
        #params = [("nonce", self._create_nonce())]
        params = {"user": self.key, "password": self.secret}
        response = self._send_request(self.info_url, params)

        if response:
            self.usd_balance = float(response["usd_balance"])
            self.btc_balance = float(response["btc_balance"])
            self.usd_reserved = float(response["usd_reserved"])
            self.btc_reserved = float(response["btc_reserved"])
            self.usd_available = float(response["usd_available"])
            self.btc_available = float(response["btc_balance"])
            self.fee = float(response["fee"])
            return 1
        return None

    def __str__(self):
        return str({"usd_balance": self.usd_balance, "btc_balance": self.btc_balance, "usd_reserved": self.usd_reserved, "btc_reserved": self.btc_reserved, "usd_available": self.usd_available, "btc_available": self.btc_available, "fee": self.fee})


if __name__ == "__main__":
    bitstamp = PrivateBitstamp()
    #bitstamp.get_info()
    print bitstamp
