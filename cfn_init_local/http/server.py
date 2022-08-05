#!/usr/bin/env python3
"""
Self contained module for serving both EC2 Metadata and CloudFormation resource Metadata.
"""
import argparse
import json
import signal
import subprocess
import sys
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread, Condition

SET_METADATA_ROUTE_CMD = "iptables -t nat -A OUTPUT -d 169.254.169.254 -j DNAT --to-destination 127.0.0.1"


class NotFoundException(Exception):
    """Exception thrown when a key is not found in the metadata object"""
    pass


class DataProducer:
    """Class to assist in parsing a User Data formatted dict"""

    def __init__(self, data):
        self._data = data

    def get_data(self, path):
        """
        Get the formatted data for the specified input path.

        The path split by "/" and then the dictionary "tree" will be descended by each
        item in the array. For example, If the path is "default/identity/foo/bar", then we will look at
        the object's metadata and first query the dict for key "default" then query that dict
        for key "identity" and so on.

        If a string instead of a dict is returned by the dict after a query, then that string will be
        returned by the function regardless of if there is more items on the path or not. This is bizarre
        behavior but directly mimics EC2 metadata behavior.

        :param path: path to query
        :return: string data for that path
        """
        path = path.strip("/")
        data = self._data
        if path != '':
            for page in path.split('/'):
                page_data = data.get(page, None)
                page_data = page_data if page_data is not None else data.get(page + "/", None)
                if page_data is None:
                    raise NotFoundException()
                data = page_data
                if isinstance(data, str):
                    return data
        return "\n".join(data.keys())  # always a dict here


class MetadataServer(BaseHTTPRequestHandler):
    """
    A mock EC2 metadata server.
    See: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html
    """

    def __init__(self, metadata, *args, **kwargs):
        self._producer = DataProducer(metadata)
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """
        Respond to HTTP GET request
        """
        try:
            data = self._producer.get_data(self.path)
        except NotFoundException:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(data.encode())

    @staticmethod
    def create_server(data, port=5000):
        """
        Create a MetadataServer serving the specified data on a specified port

        :param data: data to server
        :param port: port to serve on
        :return: HTTPServer that serves the metadata
        """
        server_address = ('', port)  # ('169.254.169.254', port)
        handler = partial(MetadataServer, data)
        return HTTPServer(server_address, handler)


class CloudFormationServer(BaseHTTPRequestHandler):
    """
    Simple HTTP server responding to CloudFormation GetStackResource requests.
    GetStackResource requests are formatted like:

    {
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
                    "Metadata": {cfn_init},
                    "LogicalResourceId": "LOGICAL_RESOURCE_ID_PLACEHOLDER"
                }
            }
        }
    }

    This server will serve the specified data regardless of any input parameters. It's ... simple
    """

    def __init__(self, data, *args, **kwargs):
        self._data = data
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """
        Respond to HTTP GET request
        """
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(self._data.encode())

    @staticmethod
    def create_server(data, port=5001):
        """
        Create a CloudFormationServer serving the specified data on a specified port.

        :param data: data to serve
        :param port: port to bind to
        :return: the HTTPServer object serving the CloudFormation content
        """
        server_address = ('', port)  # ('169.254.169.254', port)
        handler = partial(CloudFormationServer, data)
        return HTTPServer(server_address, handler)


class AsynchronousServerWrapper(object):
    """A class that helps to start an HTTPServer in a non-blocking manner as well as gracefully shut it down"""

    def __init__(self, server):
        if server is None:
            raise ValueError("server object cannot be None")
        self._server = server
        self._serving_thread = Thread(target=self.__start_server)
        # Yeah maybe we could just pass the calls straight through to the thread
        # and not have to worry about this condition/locking, but where is the fun in that
        self._condition = Condition()

    def __start_server(self):
        """
        Helper method to start a thread. Used as the execution target of the background thread
        """
        print("Starting server {}...".format(self._server))
        self._server.serve_forever()

    def serve(self):
        """
        Start the wrapped http server in a background thread
        """
        with self._condition:
            if not self._serving_thread.is_alive():
                self._serving_thread.start()

    def wait(self):
        """
        Block until the wrapped http server is shutdown
        """
        print("Waiting for thread to complete")
        with self._condition:
            if self._serving_thread.is_alive():
                self._condition.wait()
            # May consider a while loop here,
            # but if we were signaled then the condition
            # must have been notified meaning it was shutdown.
            # At least in the current implementation
            if self._serving_thread.is_alive():
                self._serving_thread.join()
            print("Thread completed")

    def shutdown(self):
        """
        Shutdown the serving thread and its server
        """
        print("Recieved shutdown signal")
        with self._condition:
            if self._serving_thread is None:
                print("Service thread does not exist")
                return
            self._server.shutdown()
            self._serving_thread.join()  # need to think about this one
            self._condition.notify()


def parse_args():
    """
    parser the command line args to this file

    :return: parsed args
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata', required=False)
    parser.add_argument('--cfn-resource', required=False)
    parser.add_argument('--container-mode', action="store_true")
    return parser.parse_args()


def mock_metadata_route():
    """
    Set the EC2 metadata route (169.254.169.254) to local host (127.0.0.1)
    """
    subprocess.run(SET_METADATA_ROUTE_CMD, shell=True, stdout=sys.stdout, stderr=sys.stderr)


def serve():
    """
    Main method. Parse command line args and start the specified servers
    """
    args = parse_args()

    metadata_port = 5000
    if args.container_mode:
        metadata_port = 80
        mock_metadata_route()

    servers = []
    if args.metadata is not None:
        # data = json.loads(get_contents_if_file(args.metadata))
        data = json.loads(args.metadata)
        servers.append(AsynchronousServerWrapper(MetadataServer.create_server(data, metadata_port)))
    if args.cfn_resource is not None:
        # data = get_contents_if_file(args.cfn_resource)
        data = args.cfn_resource
        servers.append(AsynchronousServerWrapper(CloudFormationServer.create_server(data)))

    def shutdown_servers(*args):
        for server in servers:
            server.shutdown()

    signal.signal(signal.SIGTERM, shutdown_servers)

    for server in servers:
        server.serve()

    print("Waiting for servers to finish")

    try:
        for server in servers:
            server.wait()
    except KeyboardInterrupt:
        shutdown_servers()

    print("Completed. Exiting...")


if __name__ == '__main__':
    serve()
