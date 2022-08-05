import argparse
from inspect import Signature, Parameter


class BaseDriver(object):
    """"""

    def drive(self):
        """

        :return:
        """
        parser = self.create_parser("Placeholder description")
        args = vars(parser.parse_args())
        self.execute(**args)

    def execute(self, *args, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError()

    def create_parser(self, doc=""):
        """

        :param doc:
        :return:
        """
        # I have a feeling this will ve changed but for the time being it's kinda cool
        sig = Signature.from_callable(self.execute)
        parameter_types = self.execute.__annotations__
        if len(sig.parameters) != len(parameter_types):
            raise ValueError(
                "All parameters definied in 'execute' must have types specified. See https://docs.python.org/3/library/typing.html for more")
        parser = argparse.ArgumentParser(description=doc)
        for parameter in sig.parameters.values():
            parameter_type = parameter_types[parameter.name]
            if parameter.default != Parameter.empty and parameter_type is bool:
                # if the default is specified as false then we want to store true, otherwise the opposite
                arg_options = {
                    "action": "store_true" if not parameter.default else "store_false"
                }
            elif parameter.default != Parameter.empty:
                arg_options = {
                    "default": parameter.default,
                    "required": False,
                    "type": parameter_type
                }
            else:
                arg_options = {
                    "required": True
                }
            parser.add_argument('--{}'.format(parameter.name.replace("_", "-")), **arg_options)
        return parser
