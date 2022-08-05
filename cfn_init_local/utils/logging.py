import logging

DEFAULT_FORMAT = "%(asctime)s - %(filename)s [%(levelname)s]: %(message)s"


def silence_logger(name):
    """
    Set a logger's level to critical to shut it up

    :param name: name of the logger to silence
    """
    logging.getLogger(name).setLevel(level=logging.CRITICAL)


def set_logger_class(cls):
    """
    Decorator function to set the global logging module Logger class

    :param cls: class to set
    """
    def class_decorator(func):
        def func_wrapper(*args, **kwargs):
            prevClass = logging.getLoggerClass()
            logging.setLoggerClass(cls)
            val = func(*args, **kwargs)
            logging.setLoggerClass(prevClass)
            return val

        return func_wrapper

    return class_decorator


class Logger(logging.Logger):
    """Logger wrapper class for assisting with setting handler levels"""

    def setLevel(self, level):
        """
        Set the level for the logger and its appenders

        :param level: level to set
        """
        level = getattr(logging, level.upper())
        super().setLevel(level)
        for handler in self.handlers:
            handler.setLevel(level)


class LoggerBuilder(object):
    """Factory class for creating Loggers"""

    @staticmethod
    @set_logger_class(Logger)
    def standard_console_logger(name, level="info"):
        """
        Create a Logger that logs to the console

        :param name: name of the logger
        :param level: level to set on logger
        :return: a Logger
        """
        logger = logging.getLogger(name)
        sh = logging.StreamHandler()
        sh.setFormatter(logging.Formatter(DEFAULT_FORMAT))
        logger.addHandler(sh)
        logger.setLevel(level)
        return logger
