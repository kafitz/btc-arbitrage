import datetime
import sqlite3
from observer import Observer


class Database(Observer):
    '''
    def opportunity(self, profit, volume, buyprice, kask, sellprice, kbid, perc, weighted_buyprice, weighted_sellprice):
        logging.info("profit: %f EUR with volume: %f BTC - buy at %.4f (%s) sell at %.4f (%s) ~%.2f%%" %
                     (profit, volume, buyprice, kask, sellprice, kbid, perc))
    '''
    
    def opportunity(self, profit, volume, buyprice, kask, sellprice, kbid, perc, weighted_buyprice, weighted_sellprice, available_volume, purchase_cap):
        conn = sqlite3.connect("arb.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS deals
                    (time datetime, profit float, volume float, 
                    buy_market text, buy_price float,
                    sell_market text, sell_price float, ratio float) 
                    """)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        deal = (timestamp, profit, volume, kask, buyprice, kbid, sellprice, perc)
        cursor.execute("INSERT INTO deals VALUES (?,?,?,?,?,?,?,?)", deal)
        conn.commit()