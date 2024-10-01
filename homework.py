import logging
from logging import StreamHandler
import os
import sys
import time

from dotenv import load_dotenv  # type: ignore
from telebot import TeleBot  # type: ignore
from telegram.error import TelegramError  # type: ignore
import requests  # type: ignore

from exceptions import (
    NoEnvironmentVariables, WrongAnswer, TelegramBotFailers, MessageFailure
)


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка наличия токенов и эндпоинта."""
    tokens = {'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
              'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
              'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
              'ENDPOINT': ENDPOINT,
              }
    for name, value in tokens.items():
        if not tokens['ENDPOINT']:
            raise NoEnvironmentVariables('Ошибка: ENDPOINT не определен')
        elif not value:
            logging.critical(f'Отсутствуют токен {name}')
            raise NoEnvironmentVariables(f'Отсутствуют токен {name}')

    return True


def get_api_answer(timestamp):
    """Получение API ответа.
    Функция делает запрос к единственному эндпоинту API-сервиса.
    """
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp})
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        raise WrongAnswer(f'Ошибка: {error}:')

    if response.status_code != 200:
        raise WrongAnswer(f'Ошибка: Статус не ОК {response.status_code}:')

    return response.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    try:
        homework = response['homeworks']
        logging.debug('Изменений статуса не найденно')
    except KeyError as error:
        raise KeyError(f'{error} Нет ключа homeworks в ответe')

    if not isinstance(response['homeworks'], list):
        raise TypeError(f'Ожидается список homeworks,'
                        f'но получен {type(response["homeworks"])}'
                        )
    if len(response['homeworks']) > 0:
        homework = response['homeworks'][0]

    return homework


def parse_status(homework):
    """Функция извлекает из информации о конкретной домашней работе.
    статус этой работы.
    """
    if not isinstance(homework, dict):
        raise TypeError(
            'Ожидается словарь homeworks, но получен другой тип данных'
        )
    if 'homework_name' not in homework:
        raise KeyError('Ожидается ключ homework_name')

    status = homework.get('status')
    homework_name = homework.get('homework_name')

    if status in HOMEWORK_VERDICTS:
        logging.debug(f'Статус работы такой: {status}')
        verdict = HOMEWORK_VERDICTS[status]
    else:
        raise KeyError(f'Нет такого ключа "{status}" в HOMEWORK_VERDICTS')

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Отправка сообщения в Telegram-чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug('Успешная отправка сообщения')
    except TelegramError as error:
        raise MessageFailure(f'Ошибка Telegram: {error}')
    except requests.RequestException as error:
        raise MessageFailure(f'Ошибка отправки сообщения: {error}')
    except Exception as error:
        logging.error(f'Неожиданная ошибка отправки сообщения: {error}')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        return False
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    error_sent = False
    last_message = None
    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework)
                if last_message != message:
                    send_message(bot, message)
                    last_message = message
            time.sleep(RETRY_PERIOD)
        except TelegramBotFailers as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(f'Сбой в работе программы: {error}')
            if not error_sent:
                send_message(bot, message)
                error_sent = True


if __name__ == '__main__':

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.addHandler(handler)
    handler.setFormatter(formatter)

    main()
