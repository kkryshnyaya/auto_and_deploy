import pandas as pd
import configparser
import psycopg2
from pathlib import Path

from logs import Logs


class Database:
    output_dir = None
    database = "home_store"
    host = None
    port = None
    user = None
    password = None
    table_name = "sales_data"


    # Загрузка констант и учетных данных
    @classmethod
    def load_config(cls, constants_file="constants.ini", creds_file="creds.ini"):
        config = configparser.ConfigParser()
        config.read([constants_file, creds_file], encoding="utf-8-sig")
        cls.output_dir = Path(config["Paths"]["BASE_SALE_DIR"])
        cls.host = config["Database"]["HOST"]
        cls.port = config["Database"]["PORT"]
        cls.user = config["Database"]["USER"]
        cls.password = config["Database"]["PASSWORD"]
        Logs.logger.info("Конфигурационные файлы прочитаны.")



    # Объединение .csv
    @classmethod
    def get_report(cls):
        files = list(cls.output_dir.glob("*.csv"))
        Logs.logger.info(f"Найдено csv-файлов: {len(files)}.")
        dfs = [pd.read_csv(file, encoding="utf-8-sig", delimiter=",") for file in files]
        report = pd.concat(dfs, ignore_index=True)
        Logs.logger.info("Отчет по магазинам собран.")
        return report


    # Подключение к БД
    @classmethod
    def connect(cls):
        try:
            connection = psycopg2.connect(
                database = cls.database,
                host = cls.host,
                port = cls.port,
                user = cls.user,
                password = cls.password
            )
            connection.autocommit = True # Автокоммит
            cursor = connection.cursor()
            Logs.logger.info(f"Подключение к базе данных {cls.database} установлено.")
            return connection, cursor
        except psycopg2.OperationalError:
            Logs.logger.error(f"Ошибка подключения к базе данных {cls.database}.", exc_info=True)


    # Создание таблицы
    @classmethod
    def create_table(cls, cursor):
        query = f"""CREATE TABLE if not exists {cls.table_name} (
                id serial PRIMARY KEY,
                dt date NOT NULL,
                doc_id varchar(8) NOT NULL,
                item text NOT NULL,
                category text NOT NULL,
                amount int NOT NULL,
                price int NOT NULL,
                discount int NOT NULL
        )"""
        cursor.execute(query)
        Logs.logger.info(f"Таблица {cls.table_name} создана или уже существует.")
    

    # Заполнение таблицы
    @classmethod
    def insert_table(cls, cursor, report): 
        query = f"""INSERT INTO {cls.table_name} 
            (dt, doc_id, item, category, amount, price, discount) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        data = [(row["dt"], row["doc_id"], row["item"], row["category"], row["amount"], row["price"], row["discount"]) 
                for _, row in report.iterrows()
        ] # iterrows() создает генератор строк, которые преобразуются в кортежи для каждой строки
        cursor.executemany(query, data) 
        Logs.logger.info(f"Таблица {cls.table_name} заполнена. Добавлено записей: {report.shape[0]}") 