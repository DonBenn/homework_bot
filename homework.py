import logging
from logging import StreamHandler
import os
import sys
import requests  # type: ignore
import time

from dotenv import load_dotenv  # type: ignore
from telebot import TeleBot  # type: ignore

from exceptions import (
    NoEnvironmentVariables, WrongAnswer, NotValidHomework, TelegramBotFailers
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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger.addHandler(handler)
handler.setFormatter(formatter)


def check_tokens():
    """Проверка наличия токенов и эндпоинта."""
    try:
        if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
            return True
        else:
            logging.critical('Отсутствуют необходимые токены')
            sys.exit('Ошибка: отсутствуют необходимые токены!')
    except NoEnvironmentVariables as error:
        logging.error(f'Ошибка токенов {error}')
    try:
        if not ENDPOINT:
            logging.error('Ошибка: ENDPOINT не определен')
            sys.exit('Ошибка: ENDPOINT не определен')
    except NoEnvironmentVariables as error:
        logging.error(f'Ошибка ENDPOINT: {error}')


def get_api_answer(timestamp):
    """Получение API ответа.
    Функция делает запрос к единственному эндпоинту API-сервиса.
    """
    try:
        response = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp})
        response.raise_for_status()
        if response.status_code != 200:
            logging.error(f'Ошибка: Статус не ОК {response.status_code}:')
            raise WrongAnswer(f'Ошибка: Статус не ОК {response.status_code}:')
    except requests.exceptions.HTTPError as error:
        logging.error(f'Ошибка HTTPError: {error}')
    except requests.exceptions.RequestException as error:
        logging.error(f'Ошибка RequestException: {error}')
    return response.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        logging.debug('Ожидается словарь')
        raise TypeError(
            'Ожидается словарь homeworks, но получен другой тип данных'
        )
    try:
        if not isinstance(response['homeworks'], list):
            raise TypeError(f'Ожидается список homeworks,'
                            f'но получен {type(response["homeworks"])}'
                            )
        if len(response['homeworks']) == 0:
            logging.debug('Домашняя работа не отправленна или статус'
                          ' ещё не присвоен')
            homework = response['homeworks']
        if len(response['homeworks']) > 0:
            homework = response['homeworks'][0]
            logging.debug('Домашняя работа есть')
        return homework
    except KeyError as error:
        logging.error(f'Нет ключа : {error}')
        raise ValueError('Нет ключа homeworks в ответe')


def parse_status(homework):
    """Функция извлекает из информации о конкретной домашней работе.
    статус этой работы.
    """
    try:
        if 'homework_name' not in homework:
            logging.error('Нет ключа homework_name')
            raise KeyError('Ожидается ключ homework_name')
        status = homework.get('status')
        homework_name = homework.get('homework_name')
    except NotValidHomework as error:
        logging.error(f'Ошибка: {error}')
    if status in HOMEWORK_VERDICTS:
        logging.debug(f'Статус работы такой: {status}')
        verdict = HOMEWORK_VERDICTS[status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Отправка сообщения в Telegram-чат."""
    chat_id = TELEGRAM_CHAT_ID
    try:
        bot.send_message(chat_id=chat_id, text=message)
        logging.debug('Успешная отправка сообщения')
    except Exception as error:
        logging.error(f'Ошибка сообщения: {error}')


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    error_sent = False

    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework)
                send_message(bot, message)
            time.sleep(RETRY_PERIOD)

        except TelegramBotFailers as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(f'Сбой в работе программы: {error}')
            if not error_sent:
                send_message(bot, message)
                error_sent = True


if __name__ == '__main__':
    main()
