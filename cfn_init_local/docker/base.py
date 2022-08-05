import traceback as traceback_helper
from cfn_init_local.docker.exceptions import DockerException

RESUME_CONTAINER_CMD_FORMAT = "docker start {container_id} && docker exec -it {container_id} bash"


class BasePod(object):
    """"""

    def __init__(self, containers=[]):
        self._containers = containers

    @property
    def containers(self):
        """

        :return:
        """
        return self._containers

    def add_container(self, container):
        """

        :param container:
        :return:
        """
        self._containers.append(container)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        for container in self._containers:
            container.stop()
        if traceback is not None:
            traceback_helper.print_tb(traceback)


class BaseContainer(object):
    """"""

    def __init__(self, image, run_cmd, container=None):
        self._image = image
        self._run_cmd = run_cmd
        self._container = container

    def __str__(self):
        return "Container(id={})".format(self.id)

    @property
    def id(self):
        """

        :return:
        """
        return self._container.id if self._container else None

    @property
    def image(self):
        """

        :return:
        """
        return self._image

    @property
    def run_cmd(self):
        """

        :return:
        """
        return self._run_cmd

    def set_container(self, container):
        """
        I dont love setters either
        :param container:
        :return:
        """
        self._container = container

    @property
    def resume_statement(self):
        """

        :return:
        """
        return RESUME_CONTAINER_CMD_FORMAT.format(container_id=self._container.id)

    def execute(self, *args, **kwargs):
        """
        Synchronous execution on a docker container and return the output if success
        :param args:
        :param kwargs:
        :return:
        """
        if self._container is None:
            raise ValueError("Cannot call run on a container object that has not been started")
        exit_code, output = self._container.exec_run(*args, **kwargs)
        if exit_code != 0:
            raise DockerException(exit_code, output.decode("utf-8"))
        return output.decode("utf-8")  # this assumes defaults for stream, socker, demux params to exec_run

    def stop(self):
        """

        :return:
        """
        if self._container is not None:
            self._container.stop()
