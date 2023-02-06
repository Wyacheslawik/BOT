import sqlite3

# Создание таблицы SQL
con = sqlite3.connect("guests.db")
cur = con.cursor()
sql = """\
CREATE TABLE guests (
    id_user INTEGER PRIMARY KEY AUTOINCREMENT,
    mess_id INTEGER,
    surname TEXT,
    name TEXT,
    date_b DATE,
    phone INTEGER,
    sale INTEGER

);
"""
try:
    cur.executescript(sql)
except sqlite3.DatabaseError as err:
    print('oshibka')
else:
    print('OOK')
cur.close()
con.close()


#Внесение записи в таблицу SQL
conn = sqlite3.connect("guests.db")
    cur = conn.cursor()
    t_us = (572750005,
            'Rytвкин',
            'Tячеслав',
            '1990-02-01',
            50)
    sql_t = """INSERT INTO guest (mess_id,
        surname,
        name,
        date_b,
        sale) VALUES(?, ?, ?, ?, ?)"""
    try:
        cur.execute(sql_t, t_us)
    except sqlite3.DatabaseError as err:
        print("NO", err)
    else:
        print('VNES')
        conn.commit()
    cur.close()
    conn.close()

#Считывание данных с таблицы SQL



