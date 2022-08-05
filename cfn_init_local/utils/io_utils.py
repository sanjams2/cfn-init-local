import json


class IOUtils(object):
    """"""

    @staticmethod
    def read_file(path):
        """

        :param path:
        :return:
        """
        with open(path) as fh:
            return fh.read()

    @staticmethod
    def read_json(path):
        """

        :param path:
        :return:
        """
        return json.loads(IOUtils.read_file(path))
