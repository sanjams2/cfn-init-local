import docker
from cfn_init_local import ROOT
from cfn_init_local.docker.base import BasePod
from cfn_init_local.docker.exceptions import ImageNotFoundException


class DockerClient(object):
    """"""

    def __init__(self, docker_client=None):
        self._client = docker_client or docker.from_env()

    def start_container(self, container, detach=True, cap_add=("NET_ADMIN",), tty=True):
        """

        :param container:
        :param detach:
        :param cap_add:
        :param tty:
        :return:
        """
        # Add this to debug: ports={"80/tcp":"5000", "5001/tcp":"5001"}
        if len(self._client.images.list(filters={"reference": container.image})) != 1:
            raise ImageNotFoundException("Did not find image with name '{}' in local docker repo".format(container.image))
        volumes = {ROOT + '/http/server.py': {'bind': '/var/cfn-init-local/server.py', 'mode': 'ro'}}
        docker_container = self._client.containers.run(
            container.image,
            container.run_cmd,
            detach=detach,
            cap_add=cap_add,
            tty=tty,
            volumes=volumes)
        container.set_container(docker_container)

    def create_pod(self, containers):
        """

        :param containers:
        :return:
        """
        pod = BasePod(containers)
        for container in pod.containers:
            self.start_container(container)
        return pod
