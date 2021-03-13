import api_signer
import protocol_formatter
import operation_obj

SAFE_REGIONS = [
   "af-south-1",
   "ap-east-1",
   "ap-northeast-1",
   "ap-northeast-2",
   "ap-northeast-3",
   "ap-south-1",
   "ap-southeast-1",
   "ap-southeast-2",
   "ca-central-1",
   "eu-central-1",
   "eu-north-1",
   "eu-south-1",
   "eu-west-1",
   "eu-west-2",
   "eu-west-3",
   "me-south-1",
   "sa-east-1",
   "us-east-1",
   "us-east-2",
   "us-west-1",
   "us-west-2",
]


class API:

    def __init__(self, key, service_definition):
        self._definition = service_definition
        self._latest_version = self.latest_version()
        self.protocol = self.latest()['metadata']['protocol']
        self.operations = self._make_operations_list(
            self.latest()['metadata'], 
            self.latest()['endpoints'], 
            self.latest()['shapes'], 
            self.latest()['operations']
        )
        self.endpoints = self.latest()['endpoints']

    # Returns the definiton of the lastest api version
    def latest(self):
        # Find the most recent api version
        # We can do this by sorting keys
        options = list(self._definition.keys())
        options.sort()
        return self._definition[list(reversed(options))[0]]

    # Returns the latest api version
    def latest_version(self):
        return list(self._definition.keys())[0]

    # Returns a list of the available API versions
    def api_versions(self):
        return list(self._definition.keys())

    # Returns a list of all operations
    def list_operations(self):
        return list(self.operations.keys())

    # Returns the protocol
    def get_protocol(self):
        return self.protocol

    # Returns a dictionary with all the available operations
    def _make_operations_list(self, metadata, endpoints, shapes, operations):
        to_return = {}
        for operation_name, operation in operations.items():
            to_return[operation_name] = operation_obj.Operation(metadata, endpoints, shapes, operation)

        return to_return
            


