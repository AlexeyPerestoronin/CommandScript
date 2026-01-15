import enum
import colorama


class Color(enum.Enum):
    RED = colorama.Fore.RED
    GREEN = colorama.Fore.GREEN
    YELLOW = colorama.Fore.YELLOW
    BLUE = colorama.Fore.BLUE
    MAGENTA = colorama.Fore.MAGENTA
    CYAN = colorama.Fore.CYAN
    BLACK = colorama.Fore.BLACK
    WHITE = colorama.Fore.WHITE
    RESET = colorama.Fore.RESET


class Logger:
    """
    Logger with supporting of color printing
    """

    def __init__(self, color: Color):
        self.__color = color

    def __del__(self):
        print(colorama.Style.RESET_ALL)

    def log_line(self, message: str):
        print(self.__color.value, end='')
        if message[-1] == '\n':
            print(message, end='')
        else:
            print(message, end='\n')
        print(colorama.Style.RESET_ALL, end='')
        return self


SUCCESS = Logger(Color.GREEN)
STATUS = Logger(Color.BLUE)
INFO = Logger(Color.WHITE)
WARNING = Logger(Color.YELLOW)
ERROR = Logger(Color.RED)
