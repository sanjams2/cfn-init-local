
import unittest
from cfn_init_local.http.server import DataProducer, NotFoundException


class MetadataServerTest(unittest.TestCase):

    def test_get_non_existent_key_throws_not_found_error(self):
        server = DataProducer({"foo": "bar"})
        with self.assertRaises(NotFoundException):
            server.get_data("baz")

    def test_get_key_returns_value(self):
        server = DataProducer({"foo": "bar"})
        data = server.get_data("foo")
        self.assertEqual(data, "bar")

    def test_get_key_chain_when_tailing_elements_dont_exist_returns_last_key_that_does_exist(self):
        server = DataProducer({"foo": "bar"})
        data = server.get_data("foo/biz")
        self.assertEqual(data, "bar")

    def test_get_key_whose_element_is_dict_returns_dict_keys(self):
        server = DataProducer({"foo": {"bar": "baz", "biz": "bur"}})
        data = server.get_data("foo")
        self.assertSetEqual(set(data.split("\n")), {"biz", "bar"})

