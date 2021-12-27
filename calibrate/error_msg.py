from colors import BRIGHT_RED #todo: remove this dependency
import time

# seconds to display render error message
ERROR_TIME = 2
class ErrorMessage:
    def __init__(self, text, color=BRIGHT_RED, expiry=None):
        self.expiry = expiry or time.time()+ERROR_TIME
        self.text = text
        self.color = color

    def expired(self):
        """
        Todo: timers can technically overflow after 28 days or w/e
        https://stackoverflow.com/questions/23672142/c-comparing-times-that-can-overflow
        """
          
        return time.time() - self.expiry > 0