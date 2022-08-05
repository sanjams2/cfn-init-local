
from unittest.mock import patch, Mock, call
from unittest import TestCase
from cfn_init_local.drivers.run_driver import RunDriver


TEMPLATE_NAME = "name"
TEMPLATE_BODY = "body"
DUMMY_IMAGE = "image"


@patch("cfn_init_local.drivers.run_driver.Template")
@patch("cfn_init_local.drivers.run_driver.MetadataPathFactory")
@patch("cfn_init_local.drivers.run_driver.CFNInitLocalContainer")
class TestRunDriver(TestCase):

    def setUp(self):
        self.client = Mock()
        self.entered_pod = Mock()
        self.pod = Mock()
        self.pod.__enter__ = Mock(return_value=self.pod)
        self.pod.__exit__ = Mock()
        self.client.create_pod = Mock(return_value=self.pod)
        self.stack = Mock()
        self.metadata = Mock()
        self.driver = RunDriver(self.client)

    def test_execute_when_both_runs_succeeds(self, containercls, factorycls, templatecls):
        resources = [Mock()]
        self.mock_stack(templatecls, resources)
        factory = self.mock_metadata_factory(factorycls)
        self.mock_containers_with_side_effect("success")

        self.driver.execute(TEMPLATE_NAME, TEMPLATE_BODY, DUMMY_IMAGE)

        self.verify_container_creation(containercls, resources)
        self.verify_get_metadata_calls(factory, resources)
        self.verify_template_creation_calls(templatecls)
        self.verify_run_calls([2])
        self.verify_exit_called()

    def test_execute_when_first_run_fails(self, containercls, factorycls, templatecls):
        resources = [Mock()]
        self.mock_stack(templatecls, resources)
        factory = self.mock_metadata_factory(factorycls)
        self.mock_containers_with_side_effect(ValueError)

        self.driver.execute(TEMPLATE_NAME, TEMPLATE_BODY, DUMMY_IMAGE)

        self.verify_container_creation(containercls, resources)
        self.verify_get_metadata_calls(factory, resources)
        self.verify_template_creation_calls(templatecls)
        self.verify_run_calls([1])
        self.verify_exit_called()

    def test_execute_when_first_run_fails_for_first_container_but_second_container_succeeds(self, containercls, factorycls, templatecls):
        resources = [Mock(), Mock()]
        self.mock_stack(templatecls, resources)
        factory = self.mock_metadata_factory(factorycls)
        self.pod.containers[0].run_cfn_init = Mock(side_effect=ValueError)
        self.pod.containers[1].run_cfn_init = Mock(side_effect="success")

        self.driver.execute(TEMPLATE_NAME, TEMPLATE_BODY, DUMMY_IMAGE)

        self.verify_container_creation(containercls, resources)
        self.verify_get_metadata_calls(factory, resources)
        self.verify_template_creation_calls(templatecls)
        self.verify_run_calls([1, 2])
        self.verify_exit_called()

    def test_execute_when_first_run_succeeds_and_second_run_fails(self, containercls, factorycls, templatecls):
        resources = [Mock()]
        self.mock_stack(templatecls, resources)
        factory = self.mock_metadata_factory(factorycls)
        self.mock_containers_with_side_effect(["success", ValueError])

        self.driver.execute(TEMPLATE_NAME, TEMPLATE_BODY, DUMMY_IMAGE)

        self.verify_container_creation(containercls, resources)
        self.verify_get_metadata_calls(factory, resources)
        self.verify_template_creation_calls(templatecls)
        self.verify_run_calls([2])
        self.verify_exit_called()

    def mock_stack(self, templatecls, resources):
        containers = [Mock() for _ in range(len(resources))]
        self.stack.get_resources_using_cfn_init = Mock(return_value=resources)
        templatecls.from_file_path = Mock(return_value=self.stack)
        self.pod.containers = containers

    def mock_metadata_factory(self, factorycls):
        factory = Mock()
        factory.get_metadata = Mock(return_value=self.metadata)
        factorycls.return_value = factory
        return factory

    def mock_containers_with_side_effect(self, side_effect):
        for container in self.pod.containers:
            container.run_cfn_init = Mock(side_effect=side_effect)

    def verify_container_creation(self, containercls, resources):
        calls = [call(image=DUMMY_IMAGE, metadata=self.metadata, resource=resource, stack=self.stack) for resource in resources]
        containercls.create.assert_has_calls(calls)

    def verify_run_calls(self, num_calls):
        for call_count, container in zip(num_calls, self.pod.containers):
            self.assertEqual(container.run_cfn_init.call_count, call_count)

    def verify_get_metadata_calls(self, factory, resources):
        calls = [call(resource) for resource in resources]
        factory.get_metadata.assert_has_calls(calls)

    def verify_template_creation_calls(self, templatecls):
        templatecls.from_file_path.assert_called_once_with(TEMPLATE_BODY, TEMPLATE_NAME)

    def verify_exit_called(self):
        self.assertEqual(self.pod.__exit__.call_count, 1)
