import os
from cfn_init_local.utils.io_utils import IOUtils

__ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_METADATA_PATH = __ROOT + "/../data/default/default_metadata.json"


class MetadataPathFactory(object):
    """
    Helper class for providing EC2 metadata for specific resource.

    The idea is that you can use this class to have different metadata for different resources if you so desire.
    Otherwise it will fall back to a default.
    """

    def __init__(self, paths={}):
        self._paths = paths

    def get_metadata(self, resource_id):
        """
        Get the metadata from the metadata paths passed in or use the default

        :param resource_id: resource id to get the metadata for
        :return: the EC2 metadata json string for the specified resource
        """
        metadata_path = self._paths.get(resource_id, DEFAULT_METADATA_PATH)
        return IOUtils.read_file(metadata_path)
