from datetime import datetime, timedelta
import os
import sys

from sales_generator import SalesGenerator
from database import Database
from logs import Logs


class RunScript:

    @classmethod
    def run(cls):
        try:
            Logs.setup_logs()
            Logs.delete_logs()
            Logs.logger.info("Основной скрипт начал работу.")

            # Если вчера было воскресенье, завершаем работу скрипта
            if (datetime.today() - timedelta(days=1)).weekday() == 6:
                Logs.logger.warning("Вчера было воскресенье, файлы не должны генерироваться.")
                return

            Logs.logger.info("Генерация продаж.")
            # Создается папка
            SalesGenerator.load_config()
            SalesGenerator.generate_sales()
        
            # Доп.проверка: если папка не создалась или файлы не сформировались, завершаем работу скрипта
            if not SalesGenerator.output_dir.exists() or not any(SalesGenerator.output_dir.iterdir()):
                Logs.logger.error(f"Папка {SalesGenerator.output_dir} не существует или пустая.")
                return

            Logs.logger.info("Работа с базой данных.")
            Database.load_config()
            report = Database.get_report()
            connection, cursor = Database.connect()
            try:
                Database.create_table(cursor)
                Database.insert_table(cursor, report)   
            finally:
                # Гарантированное закрытие соединения и курсора
                if cursor is not None:
                    cursor.close()
                    Logs.logger.info("Курсор закрыт.")
                if connection is not None:
                    connection.close()
                    Logs.logger.info("Соединение закрыто.")
                    Logs.logger.info("Работа с базой данных завершена.")

            # Удаляем все файлы из папки
            for file in SalesGenerator.output_dir.iterdir():
                os.remove(file)
            Logs.logger.info(f"Файлы в папке {SalesGenerator.output_dir} удалены.")

        except Exception as err:
            Logs.logger.error(f"Произошла непредвиденная ошибка.", exc_info=True)
            return
        finally:
            Logs.logger.info("Скрипт завершил работу.")


if __name__ == "__main__":
    RunScript.run()