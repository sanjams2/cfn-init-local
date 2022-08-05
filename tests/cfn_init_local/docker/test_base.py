import unittest
from unittest.mock import Mock
from cfn_init_local.docker.base import BaseContainer, BasePod
from cfn_init_local.docker.exceptions import DockerException

CMD = "cmd"
IMAGE = "image"
ID = "id"
EXPECTED_RESUME_STATEMENT = "docker start {} && docker exec -it {} bash".format(ID, ID)
OUTPUT = b"output"
EXECUTE_CMD = "execute"


class BaseContainerTest(unittest.TestCase):

	def setUp(self):
		self.docker_container = Mock()
		self.docker_container.id = ID

	def test_id_returns_none_when_no_container(self):
		container = BaseContainer(IMAGE, CMD)
		self.assertIsNone(container.id)

	def test_id_property_returns_container_id(self):
		container = BaseContainer(IMAGE, CMD, self.docker_container)
		self.assertEqual(ID, container.id)

	def test_image_property_returns_image_name(self):
		container = BaseContainer(IMAGE, CMD)
		self.assertEqual(IMAGE, container.image)

	def test_run_cmd_property_returns_run_cmd(self):
		container = BaseContainer(IMAGE, CMD)
		self.assertEqual(CMD, container.run_cmd)

	def test_set_container_sets_container_objet(self):
		# TODO
		pass

	def test_resume_statement_returns_expected_statement(self):
		container = BaseContainer(IMAGE, CMD, self.docker_container)
		self.assertEqual(EXPECTED_RESUME_STATEMENT, container.resume_statement)

	def test_execute_when_container_is_none_throws_error(self):
		container = BaseContainer(IMAGE, CMD)
		with self.assertRaises(ValueError):
			container.execute()

	def test_execute_when_non_zero_exit_code(self):
		self.docker_container.exec_run = Mock(return_value=(1, b"Error Occurred"))
		container = BaseContainer(IMAGE, CMD, self.docker_container)
		with self.assertRaises(DockerException):
			container.execute(EXECUTE_CMD)
		self.docker_container.exec_run.assert_called_once_with(EXECUTE_CMD)

	def test_execute_when_zero_exit_code(self):
		self.docker_container.exec_run = Mock(return_value=(0, OUTPUT))
		container = BaseContainer(IMAGE, CMD, self.docker_container)
		output = container.execute(EXECUTE_CMD)
		self.assertEqual(output, OUTPUT.decode("utf-8"))
		self.docker_container.exec_run.assert_called_once_with(EXECUTE_CMD)

	def test_stop_when_container_is_none_does_nothing(self):
		container = BaseContainer(IMAGE, CMD)
		container.stop()
		self.docker_container.stop.assert_not_called()

	def test_stop_calls_container_stop(self):
		container = BaseContainer(IMAGE, CMD, self.docker_container)
		container.stop()
		self.docker_container.stop.assert_called_once()


class BasePodTest(unittest.TestCase):

	def setUp(self):
		self.container = Mock()

	def test_containers_returns_containers(self):
		pod = BasePod([self.container])
		self.assertListEqual([self.container], pod.containers)

	def test_add_container_adds_container(self):
		pod = BasePod([])
		pod.add_container(self.container)
		self.assertListEqual([self.container], pod.containers)

	def test_with_clause_calls_stop_on_all_containers(self):
		with BasePod([self.container]):
			pass
		self.container.stop.assert_called_once()
