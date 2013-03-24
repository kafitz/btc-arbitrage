'''IRC module for checking balances of exhanges in "private_markets" using their assigned initials.
	Ex: 'python balance.py mtgx' for Mt.Gox'''
import sys
sys.path.append('../')
import private_markets
import config

def get_balance(input_initials):
	exchange_initials = []
	private_market_names = config.private_markets
	for market in private_market_names:
		exec('import private_markets.' + market.lower())
		market = eval('private_markets.' + str(market.lower()) + '.Private' + str(market) + '()')
		if market.initials == input_initials:
			market.get_info() # Update class variables
			return str(market) # Execute __str__ class of private market

if __name__ == "__main__":
	input_market = sys.argv[1]
	print get_balance(input_market)