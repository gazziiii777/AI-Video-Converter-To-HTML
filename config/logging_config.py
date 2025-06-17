import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logger(name):
    # Создаем папку для логов, если её нет
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Если имя логгера == "special" → пишем в special.log
    if name in ['Neuronwriter-Prompt', 'AppLogic-Prompt']:
        log_file = "logs/prompts.log"
    elif name in ['Neuronwriter-Answer', 'AppLogic-Answer']:
        log_file = "logs/answers.log"
    elif name in ['DataForSeo']:
        log_file = "logs/dataforseo.log"
    # elif name in ['Claude']:
    #     log_file = "logs/gpt.log"
    else:
        # Все остальные логи → в common.log
        log_file = "logs/app.log"

    # Обработчик для записи в нужный файл
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024 * 10,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    # Обработчик для консоли (опционально)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
