import logging
import os
import sys
import time

from dotenv import load_dotenv  # type: ignore
from telebot import TeleBot  # type: ignore
from telegram.error import TelegramError  # type: ignore
import requests  # type: ignore

from exceptions import (
    NoEnvironmentVariable, WrongAnswer
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
              }
    for name, value in tokens.items():
        if not value:
            raise NoEnvironmentVariable(f'Отсутствуют токен {name}')
    if not ENDPOINT:
        raise NoEnvironmentVariable('Ошибка: ENDPOINT не определен')

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
    if not isinstance(response, dict):
        raise TypeError(
            'Ожидается словарь response, но получен другой тип данных'
        )
    try:
        homeworks = response['homeworks']
    except KeyError as error:
        raise KeyError(f'{error} Нет ключа homeworks в ответe')

    if not isinstance(homeworks, list):
        raise TypeError(f'Ожидается список homeworks,'
                        f'но получен {type(response["homeworks"])}'
                        )

    return homeworks


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
    if 'status' not in homework:
        raise KeyError('Ожидается ключ status')

    status = homework.get('status')
    homework_name = homework.get('homework_name')

    if status not in HOMEWORK_VERDICTS:
        raise ValueError('Нет такого значения в HOMEWORK_VERDICTS')

    verdict = HOMEWORK_VERDICTS[status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Отправка сообщения в Telegram-чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug('Успешная отправка сообщения')
        return True
    except TelegramError:
        return False
    except requests.RequestException:
        return False

    except Exception as error:
        logging.error(f'Неожиданная ошибка отправки сообщения: {error}')

        return False


def main(): # noqa
    """Основная логика работы бота."""
    try:
        check_tokens()
    except NoEnvironmentVariable as error:
        logging.critical(f'Отсутствует токен: {error}')
        sys.exit(1)
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = None
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logging.debug('Изменений статуса не найденно')
                time.sleep(RETRY_PERIOD)
                continue
            homework = homeworks[0]
            message = parse_status(homework)
            if last_message != message:
                if send_message(bot, message):
                    last_message = message
                    timestamp = response['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(f'Сбой в работе программы: {error}')
            if last_message != message:
                if send_message(bot, message):
                    last_message = message
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        encoding='utf-8',
        filename='main.log',
        filemode='w'
    )

    main()
