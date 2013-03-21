btc-arbitrage
=============
(private fork of bitcoin-arbitrage)


Ideally the btc-arbitrage bot will be automated and can be controlled via irc. That means first off, we should probably
adding a hard shutdown command from the IRC interface before we ever get to live trading mode.

Live trading mode will need:
    - the ability to monitor the amounts of funds we have in each exchange so that we can focus only on trades that we
        are able to make. (so if we had $0 in mtgox and $10 in bitstamp, we would only see the trade for bitstamp -->
        intersango and not one from mtgox --> intersango)
    - the fees involved with every exchange we use. This way we can add a calculator function that will only execute    
        trades that are profitable to us after the cost of making the transaction.
    - as many exchanges as we can, concentrating on those with buy/sell APIs so we can automate the process.
