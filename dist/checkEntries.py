


import sqlite3

TN_CHARACTEREMBEDS = "CHARACTER_EMBEDS"
DB_FILEPATH = "RoutedClaims.db"
con = sqlite3.connect(DB_FILEPATH)
cur = con.cursor()




cur.execute(f'SELECT * FROM CHARACTER_EMBEDS')

print(len(cur.fetchall()))