import json
import copy
from cfn_init_local.utils.io_utils import IOUtils

CLOUD_INIT_FIELD_NAME = "AWS::CloudFormation::Init"
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
                "Metadata": None,
                "LogicalResourceId": "LOGICAL_RESOURCE_ID_PLACEHOLDER"
            }
        }
    }
}


class Resource(object):
    """Class representing cloudformation resource
    (https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/resources-section-structure.html)"""

    def __init__(self, name, body):
        self._name = name
        self._body = body
        data = self._body.get("Metadata", {}).get(CLOUD_INIT_FIELD_NAME, None)
        self._cfn_init = data and {CLOUD_INIT_FIELD_NAME: data}
        response = copy.deepcopy(DESCRIBE_STACK_RESOURCE_RESPONSE)
        response["DescribeStackResourceResponse"]["DescribeStackResourceResult"]["StackResourceDetail"]["Metadata"] = \
            json.dumps(self._cfn_init)
        self._response = self._cfn_init and json.dumps(response)

    def __str__(self):
        return self._name

    @property
    def cfn_init(self):
        """
        Get the CfnInit property or a resource if it exists.

        :return: cfn init if exists
        """
        return self._cfn_init

    @property
    def name(self):
        """
        Get the name of a resource. Also known as logical id

        :return: name of resource
        """
        return self._name

    @property
    def describe_stack_resource_response(self):
        return self._response


class Template(object):
    """Class representing cloudformation template
    (https://aws.amazon.com/cloudformation/aws-cloudformation-templates/)"""

    def __init__(self, name, body):
        self._name = name
        self._body = body

    @property
    def name(self):
        """
        Get the template name

        :return: name of the template
        """
        return self._name

    @property
    def body(self):
        """
        Get the template body

        :return: body of the template
        """
        return self._body

    @staticmethod
    def from_file_path(file_path, name):
        """
        Create a template object from a specified file path

        :param file_path: file path to read from
        :param name: name of the template
        :return: template
        """
        return Template(name, IOUtils.read_json(file_path))

    def get_resources_using_cfn_init(self):
        """
        Get resource objects representing all the resources in a stack that use CfnInit

        :return: list of resource objects using cfn init
        """
        resources = []
        for resource_name, resource_body in self._body.get('Resources', {}).items():
            cfn_resource = Resource(resource_name, resource_body)
            if cfn_resource.cfn_init is not None:
                resources.append(cfn_resource)
        return resources
