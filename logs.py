import configparser
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path


class Logs:
    log_dir = None
    logger = None

    # Настройка логирования
    @classmethod
    def setup_logs(cls, constants_file="constants.ini"):
        today = datetime.today().strftime("%Y-%m-%d")

        config = configparser.ConfigParser()
        config.read(constants_file, encoding="utf-8-sig")
        cls.log_dir = Path(config["Paths"]["BASE_LOG_DIR"])
        cls.log_dir.mkdir(exist_ok=True)
        log_file = cls.log_dir/f"{today}.log"

        logging.basicConfig(
            level = logging.INFO,
            format = "%(asctime)s - %(levelname)s - %(message)s",
            datefmt = "%Y-%m-%d %H:%M:%S",                        
            handlers = [logging.FileHandler(log_file)]
        )
        cls.logger = logging.getLogger()
        cls.logger.info("Настройка логгера завершена.")
        cls.logger.info("Папка logs создана или уже существует.")
        cls.logger.info(f"Файл {today}.log создан.")
        

    # Удаление старых логов, оставляем логи за последнюю неделю
    @classmethod
    def delete_logs(cls, required_days=7):
        delete_file_flag = False
        threshold_date = datetime.today() - timedelta(days=required_days) # Пороговая дата 
        
        all_log_files = list(cls.log_dir.glob("*.log"))      
        for log_file in all_log_files:
            date_part = log_file.stem                                     # Имя файла без расширения
            file_date = datetime.strptime(date_part, "%Y-%m-%d")
            # Если файл старше пороговой даты - удаляем
            if file_date < threshold_date:
                delete_file_flag = True
                os.remove(str(log_file))                                  # Аргумент - строка, а не объект Path
                cls.logger.info(f"Файл {date_part}.log удален.")           
        if not delete_file_flag:
            cls.logger.info("Файлы логов для удаления отсутствуют.")