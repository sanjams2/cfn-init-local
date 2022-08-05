

class DockerException(Exception):
    """"""

    def __init__(self, code, msg):
        self._code = code
        self._msg = msg

    def __str__(self):
        return "Exit Code: {}; Message: {}".format(self._code, self._msg)


class ImageNotFoundException(Exception):
    """"""
    pass
