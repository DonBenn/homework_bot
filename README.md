# Telegram-бот homework_bot

Telegram-бот, который обращается к API сервиса Практикум Домашка и узнаёт статус  домашней работы. Раз в 10 минут бот опрашивает API сервиса и проверяет статус. При обновлении статуса, отправляет соответствующее уведомление в Telegram. Все операции логируются.

## Используемые технологии:

Python 3.9, Python-telegram-bot, pyTelegramBotAPI, Requests, python-dotenv


## Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/DonBenn/homework_bot.git
```

```
cd homework_bot
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source venv/Scripts/activate
```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Создайте файл .evn:
```
touch .evn
```

В файле `.evn` Создайте переменные указанные в файле `env.example`

Получить токен можно по адресу: <https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a>

### Запустить проект:

```
python homework.py
```
