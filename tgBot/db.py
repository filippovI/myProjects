import sqlite3 as sl
import telebot as tb
import config as cfg
import utils as ut

bot = tb.TeleBot(cfg.token)


# Декоратор для БД
def db_connection(func):
    def inner(*args, **kwargs):
        with sl.connect('server.db', check_same_thread=False) as db:
            res = func(*args, db=db, **kwargs)
        return res

    return inner


# Создание таблиц и заполнения валют при запуске (если их нет)
@db_connection
def init_db(db):
    sql = db.cursor()
    sql.execute("""CREATE TABLE IF NOT EXISTS currencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            value TEXT,
            rus_value TEXT
            )""")

    # Создание таблицы с валютыми, которые уйдут в запрос
    sql.execute("""CREATE TABLE IF NOT EXISTS val_for_convert (
            ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            currency TEXT
            )""")

    # Создание таблицы с логами
    sql.execute("""CREATE TABLE IF NOT EXISTS logs (
                ID INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                time TEXT,
                error_handled TEXT,
                error TEXT,
                user TEXT
                )""")

    # Загрузка изначальных валют
    sql.execute("""INSERT INTO currencies(VALUE, RUS_VALUE) SELECT * FROM (SELECT 'USD','Доллар') AS tmp
                           WHERE NOT EXISTS (SELECT value FROM currencies WHERE value='USD');
                          """)

    sql.execute("""INSERT INTO currencies(VALUE, RUS_VALUE) SELECT * FROM (SELECT 'EUR','Евро') AS tmp
                           WHERE NOT EXISTS (SELECT value FROM currencies WHERE value='EUR');
                          """)

    sql.execute("""INSERT INTO currencies(VALUE, RUS_VALUE) SELECT * FROM (SELECT 'RUB','Рубль') AS tmp
                           WHERE NOT EXISTS (SELECT value FROM currencies WHERE value='RUB');
                          """)


# Функция для получения информации из таблицы
@db_connection
def get_info(db, table: str, col: str):
    sql = db.cursor()
    return sql.execute("""SELECT {0} FROM {1}""".format(col, table))


# Функция для получения количества записей в таблице
@db_connection
def get_len_info(db, table: str, col: str):
    sql = db.cursor()
    sql.execute("""SELECT {0} FROM {1}""".format(col, table))
    return len(sql.fetchall())


# Функция для заполнения таблицы
@db_connection
def insert_table(db, table: str, col: str, value):
    sql = db.cursor()
    value_str = ''
    m = len(value)

    # Цикл для преобразования списка в строку виду a = "'b','c'"
    for v, i in enumerate(value):
        if v < m - 1:
            value_str = value_str + '"' + i + '",'
        else:
            value_str = value_str + '"' + i + '"'
    sql.execute("""INSERT INTO {0}({1}) VALUES({2})""".format(table, col, value_str))


# Функция для удаления данных из таблицы
@db_connection
def delete_table(db, table: str, admin=False, msg=None):
    try:
        sql = db.cursor()
        sql.execute("""DELETE FROM {0}""".format(table))
        sql.execute("""DELETE FROM sqlite_sequence where name='{0}'""".format(table))
        if admin:
            bot.send_message(msg.chat.id, 'Таблица {0} очищена'.format(msg.text))
    except sl.OperationalError as err:
        bot.send_message(msg.chat.id, 'Ошибка')
        ut.Logging.write_log(msg, 'Ошибка удаление из таблицы {0}'.format(table), err)


init_db()
