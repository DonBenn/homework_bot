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


class NotValidHomework(Exception):
    """Класс в котором проверяются все исключения если переменная
    homework не корректная
    """
    pass


class TelegramBotFailers(Exception):
    """Класс в котором обрабатываются все сбои в работе бота """
    pass
