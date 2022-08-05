
from cfn_init_local.docker.base import BaseContainer

START_SERVER_CMD_FORMAT = "/usr/bin/env python3 /var/cfn-init-local/server.py" \
                          " --metadata '{metadata}'" \
                          " --cfn-resource '{resource}'" \
                          " --container-mode"
CFN_INIT_MOCK_SERVER_URL = "http://127.0.0.1:5001"
CFN_INIT_CMD_FORMAT = "/opt/aws/bin/cfn-init -v --stack {stack} --resource {resource} --url {url}"


class CFNInitLocalContainer(BaseContainer):
    """Specialized version of a BaseContainer with logic specifically for cfn-init-local"""

    def __init__(self, image, run_cmd, container=None, resource=None, stack=None):
        super().__init__(image, run_cmd, container)
        self._resource = resource
        self._stack = stack

    def __str__(self):
        container_id = self._container.id if self._container else None
        return "Container(id={}, stack={}, resource={})".format(container_id, self._stack, self._resource)

    @staticmethod
    def create(image, metadata, resource, stack):
        """
        Helper method for creating a standard cfn-init-local container.
        Uses a formatted version of START_SERVER_CMD_FORMAT as the run_cmd

        :param image: image to use for the container
        :param metadata: the EC2 metadata for this container (dict)
        :param resource: the resource this container is mocking
        :param stack: the stack the resource belongs to
        :return: a container
        """
        run_cmd = START_SERVER_CMD_FORMAT.format(metadata=metadata, resource=resource.describe_stack_resource_response)
        return CFNInitLocalContainer(image, run_cmd, None, resource, stack)

    def run_cfn_init(self):
        """
        Wrapper method to execute the cfn-init command within the container

        :return: the execution result
        """
        return self.execute(
            CFN_INIT_CMD_FORMAT.format(stack=self._stack.name, resource=self._resource.name, url=CFN_INIT_MOCK_SERVER_URL))

    @property
    def stack(self):
        """
        Stack the resource this container represents belongs to

        :return: the stack
        """
        return self._stack

    @property
    def resource(self):
        """
        The resource this container represents

        :return: the resource
        """
        return self._resource
