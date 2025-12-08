import pandas as pd
import numpy as np
import random
import secrets # Генерация криптографически безопасных значений
import string  # Содержит готовые строки символов
import configparser
from pathlib import Path
from datetime import datetime, timedelta
import os

from logs import Logs


class SalesGenerator:
    num_shops = None     # Кол-во магазинов
    min_cashes = None    # Кол-во касс в магазине
    max_cashes = None
    min_checks = None    # Кол-во чеков в кассе
    max_checks = None
    min_items = None     # Кол-во товаров в чеке
    max_items = None
    min_amount = None    # Кол-во единиц каждого товара
    max_amount = None
    min_price = None     # Цена товара
    max_price = None
    min_discount = None  # Процент скидки
    max_discount = None
    categories = None    # Категория товара
    items = {}           # Наименование товара
    output_dir = None    # Папка для выгрузок
    yesterday = None     # Вчера
    doc_ids = set()      # Уникальные идентификаторы чеков 


    # Загрузка констант
    @classmethod
    def load_config(cls, constants_file="constants.ini"):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        constants_path = os.path.join(BASE_DIR, constants_file)

        config = configparser.ConfigParser()
        config.read(constants_path, encoding="utf-8-sig")

        cls.num_shops = config.getint("Ranges", "NUM_SHOPS")
        cls.min_cashes = config.getint("Ranges", "MIN_CASHES")
        cls.max_cashes = config.getint("Ranges", "MAX_CASHES")
        cls.min_checks = config.getint("Ranges", "MIN_CHECKS")
        cls.max_checks = config.getint("Ranges", "MAX_CHECKS")
        cls.min_items = config.getint("Ranges", "MIN_ITEMS")
        cls.max_items = config.getint("Ranges", "MAX_ITEMS")
        cls.min_amount = config.getint("Ranges", "MIN_AMOUNT")
        cls.max_amount = config.getint("Ranges", "MAX_AMOUNT")
        cls.min_price = config.getint("Ranges", "MIN_PRICE")
        cls.max_price = config.getint("Ranges", "MAX_PRICE")
        cls.min_discount = config.getint("Ranges", "MIN_DISCOUNT")
        cls.max_discount = config.getint("Ranges", "MAX_DISCOUNT")
        cls.categories = [x.strip() for x in config["Goods"]["CATEGORIES"].split(",")]
        for category in cls.categories:
            key = "ITEMS_" + category.replace(" ", "_")
            goods_raw = config["Goods"][key]
            cls.items[category] = [x.strip() for x in goods_raw.split(",")]

        cls.output_dir = Path(os.path.join(BASE_DIR, config["Paths"]["BASE_SALE_DIR"]))
        # cls.output_dir = Path(config["Paths"]["BASE_SALE_DIR"])
        cls.output_dir.mkdir(exist_ok=True)
        cls.yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        Logs.logger.info("Конфигурационный файл прочитан.")


    # Генерация уникальных doc_id
    @classmethod
    def make_unique_ids(cls, length=8):
        alphabet = string.ascii_uppercase + string.digits                     # Буквенно-цифровой набор
        while True:                                                           # Повтор цикла до тех пор, пока не найдется уник id
            doc_id = ''.join(secrets.choice(alphabet) for _ in range(length)) # Выбор случайного элемента
            if doc_id not in cls.doc_ids:
                cls.doc_ids.add(doc_id)
                return doc_id


    # Генерация файлов (используется make_unique_ids)
    @classmethod
    def generate_sales(cls):
        # Для каждого магазина вычисляем кол-во касс
        for shop_num in range(1, cls.num_shops+1):                           
            num_cashes = np.random.randint(cls.min_cashes, cls.max_cashes+1)
            # Для каждой кассы вычисляем кол-во чеков
            for cash_num in range(1, num_cashes+1):
                num_checks = np.random.randint(cls.min_checks, cls.max_checks+1)
                # Список словарей для каждой кассы каждого магазина (1 строка - 1 товар в чеке)
                rows = [] 
                # Для каждого чека вычисляем кол-во строк (товаров)
                for _ in range(num_checks):
                    num_items = np.random.randint(cls.min_items, cls.max_items+1)
                    doc_id = cls.make_unique_ids()
                    # Для каждой строки чека вычисляем:
                    for _ in range(num_items):
                        category = random.choice(cls.categories)                                         # Категория
                        item = random.choice(cls.items[category])                                        # Товар
                        amount = np.random.randint(cls.min_amount, cls.max_amount+1)                     # Кол-во единиц конкретного товара
                        price = np.random.randint(cls.min_price, cls.max_price+1)                        # Цена товара
                        discount_percent = np.random.randint(cls.min_discount, cls.max_discount+1) / 100 # Процент скидки
                        discount = round(price * discount_percent)                                       # Сумма скидки
                        rows.append({
                            "dt": cls.yesterday,
                            "doc_id": doc_id,
                            "item": item,
                            "category": category,
                            "amount": amount,
                            "price": price,
                            "discount": discount
                        })
                df = pd.DataFrame(rows)
                filename = f"{shop_num}_{cash_num}.csv"
                df.to_csv(cls.output_dir / filename, encoding="utf-8-sig", index=False)
        Logs.logger.info(f"Генерация продаж завершена. Файлы в папке: {cls.output_dir}")