class NoEnvironmentVariables(Exception):
    """Класс в котором проверяются все исключения отсутсвия переменных
    окружения
    """
    pass


class WrongAnswer(Exception):
    """Класс в котором проверяются все исключения отсутсвия ожидаеммого
    положительного ответа
    """
    pass


class MessageFailure(Exception):
    """Класс в котором проверяются исключения если отправка
    сообщения не корректная
    """
    pass


class TelegramBotFailers(Exception):
    """Класс в котором обрабатываются все сбои в работе бота """
    pass
