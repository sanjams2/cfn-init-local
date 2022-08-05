import unittest
from unittest.mock import Mock, call
from cfn_init_local import ROOT
from cfn_init_local.docker.resources import BaseContainer
from cfn_init_local.docker.client import DockerClient
from cfn_init_local.docker.exceptions import ImageNotFoundException

IMAGE = "image"
CMD = "cmd"
ID = 1

EXPECTED_RUN_CMD_ARGS = (
    IMAGE,
    CMD,
)
EXPECTED_RUN_CMD_KWARGS= dict(
    detach=True,
    cap_add=("NET_ADMIN",),
    tty=True,
    volumes={ROOT + '/http/server.py': {'bind': '/var/cfn-init-local/server.py', 'mode': 'ro'}}
)


class DockerClientTest(unittest.TestCase):

    def setUp(self):
        self.docker = Mock()
        self.docker_container = Mock()
        self.docker_container.id = ID
        self.docker.containers.run = Mock(return_value=self.docker_container)
        self.client = DockerClient(self.docker)

    def test_start_container_when_image_exists(self):
        self.docker.images.list = Mock(return_value=[IMAGE])
        container = BaseContainer(IMAGE, CMD)

        self.client.start_container(container)

        self.assertEqual(container.id, ID)
        self.docker.images.list.assert_called_once_with(filters={"reference": IMAGE})
        self.docker.containers.run.assert_called_once_with(*EXPECTED_RUN_CMD_ARGS, **EXPECTED_RUN_CMD_KWARGS)

    def test_start_container_when_image_does_not_exists_throws_error(self):
        self.docker.images.list = Mock(return_value=[])
        container = BaseContainer(IMAGE, CMD)

        with self.assertRaises(ImageNotFoundException):
            self.client.start_container(container)

        self.docker.images.list.assert_called_once_with(filters={"reference": IMAGE})

    def test_create_pod_starts_containers_and_populates_container_property(self):
        self.docker.images.list = Mock(return_value=[IMAGE])
        num_containers = 2
        containers = [BaseContainer(IMAGE, CMD) for _ in range(num_containers)]

        pod = self.client.create_pod(containers)

        for i in range(num_containers):
            self.assertEqual(containers[i].id, ID)
        list_calls = [call(filters={"reference": IMAGE}) for _ in range(num_containers)]
        self.docker.images.list.assert_has_calls(list_calls)
        run_calls = [call(*EXPECTED_RUN_CMD_ARGS, **EXPECTED_RUN_CMD_KWARGS)]
        self.docker.containers.run.assert_has_calls(run_calls)
        self.assertListEqual(pod.containers, containers)

