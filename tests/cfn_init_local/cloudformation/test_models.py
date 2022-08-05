
import unittest
import json
from unittest.mock import patch
from cfn_init_local.utils.io_utils import IOUtils
from cfn_init_local.cloudformation.models import Resource, Template

NAME = "name"
CFN_INIT_DATA = "data"
BODY = {"hello": "world"}
CFN_INIT_SECTION = {"AWS::CloudFormation::Init": CFN_INIT_DATA}
BODY_WITH_CFN_INIT = {"Metadata": CFN_INIT_SECTION}
FILE_PATH = "/tmp/mockfilepath"
BODY_WITH_ONE_RESOURCE_USING_CFN_INIT = {
	"Resources":{
		"ResourceWithCfnInit": BODY_WITH_CFN_INIT,
		"ResourceWithoutCfnInit": {}
	}
}
BODY_WITH_NO_RESOURCES_USING_CFN_INIT = {"Resources": {"ResourceWithoutCfnInit": {}}}
DESCRIBE_STACK_RESOURCE_RESPONSE = {
	"DescribeStackResourceResponse": {
		"DescribeStackResourceResult": {
			"StackResourceDetail": {
				"StackId": "STACK_ID_PLACEHOLDER",
				"ResourceStatus": "CREATE_COMPLETE",
				"DriftInformation": {
					"StackResourceDriftStatus": "NOT_CHECKED"
				},
				"ResourceType": "RESOURCE_TYPE_PLACEHOLDER",
				"LastUpdatedTimestamp": 1557817451.95397,
				"StackName": "STACK_NAME_PLACEHOLDER",
				"PhysicalResourceId": "PHYSICAL_RESOURCE_ID_PLACEHOLDER",
				"Metadata": json.dumps(CFN_INIT_SECTION),
				"LogicalResourceId": "LOGICAL_RESOURCE_ID_PLACEHOLDER"
			}
		}
	}
}


class ResourceTest(unittest.TestCase):

	def test_name_returns_name(self):
		resource = Resource(NAME, {})
		self.assertEqual(resource.name, NAME)

	def test_cfn_init_returns_none_when_no_cfn_init_in_body(self):
		resource = Resource(NAME, {})
		self.assertIsNone(resource.cfn_init)

	def test_cfn_init_returns_correct_object_when_cfn_init_in_body(self):
		resource = Resource(NAME, BODY_WITH_CFN_INIT)
		self.assertDictEqual(resource.cfn_init, {"AWS::CloudFormation::Init": CFN_INIT_DATA})

	def test_describe_stack_resource_response_returns_response_with_cfn_init_embeded(self):
		resource = Resource(NAME, BODY_WITH_CFN_INIT)
		# using json.loads so the DESCRIBE_STACK_RESOURCE_RESPONSE can be an easier to read dict
		self.assertEqual(json.dumps(DESCRIBE_STACK_RESOURCE_RESPONSE), resource.describe_stack_resource_response)


class TemplateTest(unittest.TestCase):

	def test_name_returns_name(self):
		template = Template(NAME, {})
		self.assertEqual(template.name, NAME)

	@patch.object(IOUtils, "read_json")
	def test_from_file_reads_json_from_specified_path(self, mock_read_json_method):
		mock_read_json_method.return_value = BODY
		template = Template.from_file_path(FILE_PATH, NAME)
		self.assertEqual(template.name, NAME)
		self.assertDictEqual(template.body, BODY)

	def test_get_resources_using_cfn_init_returns_no_resources_when_none_use_cfn_init(self):
		template = Template(NAME, BODY_WITH_NO_RESOURCES_USING_CFN_INIT)
		resources = template.get_resources_using_cfn_init()
		self.assertEqual(len(resources), 0)

	def test_get_resources_using_cfn_init_returns_resources_when_some_use_cfn_init(self):
		template = Template(NAME, BODY_WITH_ONE_RESOURCE_USING_CFN_INIT)
		resources = template.get_resources_using_cfn_init()
		self.assertEqual(len(resources), 1)
		self.assertEqual(type(resources[0]), Resource)
