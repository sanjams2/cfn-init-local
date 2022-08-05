import unittest
from unittest.mock import Mock
from cfn_init_local.docker.resources import CFNInitLocalContainer

IMAGE = "image"
RUN_CMD = "run_cmd"
METADATA = {"metadata": "metadata"}
CFN_RESOURCE_DATA = {"cfn_data": "cfn_data"}
EXPECTED_START_SERVER_CMD_FORMAT = "/usr/bin/env python3 /var/cfn-init-local/server.py" \
                                   " --metadata '{metadata}'" \
                                   " --cfn-resource '{resource}'" \
                                   " --container-mode"
EXPECTED_CFN_INIT_CMD_FORMAT = "/opt/aws/bin/cfn-init -v --stack {stack} --resource {resource} --url http://127.0.0.1:5001"


class TestCFNInitLocalContainer(unittest.TestCase):

    def setUp(self):
        self.resource = Mock()
        self.resource.describe_stack_resource_response = CFN_RESOURCE_DATA
        self.stack = Mock()

    def test_create(self):
        container = CFNInitLocalContainer.create(IMAGE, METADATA, self.resource, self.stack)
        self.assertEqual(container.image, IMAGE)
        expected_run_cmd = EXPECTED_START_SERVER_CMD_FORMAT.format(metadata=METADATA, resource=CFN_RESOURCE_DATA)
        self.assertEqual(container.run_cmd, expected_run_cmd)
        self.assertEqual(container.resource, self.resource)
        self.assertEqual(container.stack, self.stack)

    def test_run_cfn_init(self):
        docker_container = Mock()
        docker_container.exec_run = Mock(return_value=(0, b"result"))
        self.resource.name = "resource"
        self.stack.name = "stack"

        container = CFNInitLocalContainer(IMAGE, RUN_CMD, docker_container, self.resource, self.stack)

        result = container.run_cfn_init()
        self.assertEqual(result, "result")
        expected_cmd = EXPECTED_CFN_INIT_CMD_FORMAT.format(stack="stack", resource="resource")
        docker_container.exec_run.assert_called_once_with(expected_cmd)


