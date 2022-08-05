from cfn_init_local.cloudformation.models import Template
from cfn_init_local.docker.client import DockerClient
from cfn_init_local.docker.resources import CFNInitLocalContainer
from cfn_init_local.drivers import BaseDriver
from cfn_init_local.utils.data_utils import MetadataPathFactory
from cfn_init_local.utils.logging import LoggerBuilder

LOGGER = LoggerBuilder.standard_console_logger(__file__)

DEFAULT_CFN_INIT_LOCAL_IMAGE_TAG = "cfn-init-local"


class RunDriver(BaseDriver):
    """"""

    def __init__(self, docker_client=None):
        self._client = docker_client or DockerClient()

    def execute(self, template_name: str, template_body: str,image: str, metadata_paths: dict = {},
                verbose: bool = False):
        """


        :param template_name:
        :param template_body:
        :param image:
        :param metadata_paths:
        :param verbose:
        :return:
        """
        if verbose:
            LOGGER.setLevel("debug")

        stack = Template.from_file_path(template_body, template_name)
        metadata_factory = MetadataPathFactory(metadata_paths)

        LOGGER.info("Starting CfnInitLocal...")
        with self.__create_pod(stack, image, metadata_factory) as pod:
            for container in pod.containers:
                # Run 1
                LOGGER.debug("Created container for resource '%s' with id '%s'. Running cfn-init", container.resource,
                             container.id)
                try:
                    container.run_cfn_init()
                except Exception as e:
                    LOGGER.error("Recieved exception trying to call cfn-init for resource '%s'", container.resource)
                    LOGGER.error(e)
                    continue
                LOGGER.info("First run of cfn-init passed for resource '%s'", container.resource)

                # Run 2
                LOGGER.debug("Executing second run of cfn-int on container '%s' for an idempotency check", container.id)
                try:
                    container.run_cfn_init()
                except Exception as e:
                    LOGGER.error("Recieved exception trying to call cfn-init a second time for resource '%s'",
                                 container.resource)
                    LOGGER.error(e)
                LOGGER.info("Second run of cfn-init passed for resource '%s'", container.resource)

            # Output helper message
            RunDriver.__output_container_resume_statements(pod.containers)
            LOGGER.info("Stopping containers")
        LOGGER.info("Completed CfnInitLocal")

    def __create_pod(self, stack, image, metadata_factory):
        """

        :param stack:
        :param image:
        :param metadata_factory:
        :return:
        """
        containers = []
        for resource in stack.get_resources_using_cfn_init():
            containers.append(
                CFNInitLocalContainer.create(
                    image=image,
                    metadata=metadata_factory.get_metadata(resource),
                    resource=resource,
                    stack=stack
                )
            )
        return self._client.create_pod(containers)

    @staticmethod
    def __output_container_resume_statements(containers):
        """

        :param containers:
        :return:
        """
        if len(containers) == 0:
            return
        commands = "\n\n".join(
            ["{}:\n{}\n".format(container.resource, container.resume_statement) for container in containers])
        LOGGER.info("Run the following commands to inspect each resource's container:\n\n%s", commands)
