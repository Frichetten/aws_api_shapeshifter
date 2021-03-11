import boto3
import socket
import re

from xeger import Xeger

import api_signer
import protocol_formatter

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

DEFAULT_HEADERS = {
    'content-type': '',
    'host': '',
    'x-amz-date': '',
}

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

    # Returns a dictionary with all the available operations
    def _make_operations_list(self, metadata, endpoints, shapes, operations):
        to_return = {}
        for operation_name, operation in operations.items():
            to_return[operation_name] = Operation(metadata, endpoints, shapes, operation)

        return to_return
            

class Operation:

    def __init__(self, metadata, endpoints, shapes, operation):
        self.name = operation['name']
        self.method = operation['http']['method']
        self.request_uri = operation['http']['requestUri']
        self.endpoints = endpoints
        self.input_format = self._parse_input_shape(self.name, shapes, operation)

        self.endpoint_prefix = metadata['endpointPrefix']

        ## v2
        self.metadata = metadata

        if 'targetPrefix' in metadata.keys(): 
            self.target_prefix = metadata['targetPrefix']
        else:
            self.target_prefix = metadata['endpointPrefix']

        # Not every API has these fields
        if 'input' in operation.keys():
            self.input = operation['input']['shape']
            
        if 'output' in operation.keys():
            self.output = operation['output']['shape']

    def make_request(self, 
        credentials='',
        access_key='',
        secret_key='',
        token='',
        method='',
        endpoint_prefix='',
        host='',
        region='',
        endpoint='',
        content_type='',
        amz_target='',
        request_uri='',
        request_map='',
    ):
        if credentials == '' and access_key == '':
            raise Exception('Lack of Credentials')
        if credentials != '':
            access_key = credentials.access_key
            secret_key = credentials.secret_key
            token = credentials.token
        if endpoint_prefix == '':
            endpoint_prefix = self.endpoint_prefix
        if method == '':
            method = self.method
        if region == '':
            if "us-east-1" in self.endpoints['endpoints'].keys():
                region = "us-east-1"
            else:
                chosen_region = list(self.endpoints['endpoints'].keys())[0]
                if "hostname" in self.endpoints['endpoints'][chosen_region].keys():
                    region = self.endpoints['endpoints'][chosen_region]['credentialScope']['region']
                    host = self.endpoints['endpoints'][chosen_region]['hostname']
                else:
                    region = chosen_region
        if host == '':
            # ce ruins all of this
            if "isRegionalized" in self.endpoints.keys():
                regions = list(self.endpoints['endpoints'].keys())
                if self._has_safe_regions(regions):
                    host = endpoint_prefix + "." + self._get_safe_region(regions) + '.amazonaws.com'
                else:
                    if self._test_hostname(endpoint_prefix + ".us-east-1.amazonaws.com" ):
                        host = endpoint_prefix + ".us-east-1.amazonaws.com"
                    else:
                        host = endpoint_prefix + '.amazonaws.com'
            else:
                host = endpoint_prefix + "." + region + '.amazonaws.com'
        if endpoint == '':
            endpoint = 'https://' + host
        if content_type == '':
            content_type = 'application/x-amz-json-1.1' 
        if amz_target == '':
            amz_target = self.target_prefix + "." + self.name
        if request_uri == '':
            request_uri = self.request_uri

        ## v2 - gather body from shape
        if request_map == '':
            request_map = { 'Action': self.name }
            request_map['Version'] = self.metadata['apiVersion']
            # Do something with self.input_format
            request_map.update(self.input_format)

        if content_type != '':
            headers = { 'Content-Type': content_type }

        # Depending on the protocol we need to format inputs differently
        if self.metadata['protocol'] == "query":
            formatted_request = protocol_formatter.query_protocol_formatter(
                method,
                host,
                token,
                request_map,
            )
            response = api_signer.query_signer(
                access_key=access_key,
                secret_key=secret_key,
                token=token,
                method=method,
                endpoint_prefix=endpoint_prefix,
                host=host,
                region=region,
                endpoint=endpoint,
                content_type=content_type,
                amz_target=amz_target,
                request_uri=request_uri,
                request_map=formatted_request
            )
            return response
        if self.metadata['protocol'] == "json":
            formatted_request = protocol_formatter.query_protocol_formatter(
                method,
                host,
                token,
                request_map,
                headers=headers
            )
            response = api_signer.json_signer(
                access_key=access_key,
                secret_key=secret_key,
                token=token,
                method=method,
                endpoint_prefix=endpoint_prefix,
                host=host,
                region=region,
                endpoint=endpoint,
                content_type=content_type,
                amz_target=amz_target,
                request_uri=request_uri,
                request_map=formatted_request
            )
            return response


        return response
        
    def _has_safe_regions(self, regions):
        # return true if it has safe regions
        # false if not
        for region in regions:
            if region in SAFE_REGIONS:
                return True
        return False

    def _get_safe_region(self, regions):
        for region in regions:
            if region in SAFE_REGIONS:
                return region

    def _test_hostname(self, hostname):
        try:
            socket.gethostbyname(hostname)
            return True
        except socket.error:
            return False

    def _parse_input_shape(self, name, shapes, operation):
        to_return = {}

        # Not every operation has an input
        if 'input' in operation.keys():
            input_shape_name = operation['input']['shape']
            shape = shapes[input_shape_name]
             
            # We now have the shape definition
            # We need to populate the required fields
            if 'required' in shape.keys():
                for member in shape['required']:
                    # Need to get member name
                    member_name = shape['members'][member]['shape']
                    # TODO: We are only supporting string types right now.
                    # It will take a good amount of effort to implement all of them
                    member_shape = shapes[member_name]
                    if member_shape['type'] == "string":
                        to_return[member] = self._gen_string_shape(member_shape)
                    elif shapes[member_name]['type'] == "integer":
                        to_return[member] = 1
                    elif shapes[member_name]['type'] == "boolean":
                        to_return[member] = "false"

                return to_return
        return ""

    def _gen_string_shape(self, member_shape):
        # min, max, pattern, enum
        if "pattern" in member_shape.keys():
            return self._gen_regex_pattern(member_shape['pattern'])
        if "enum" in member_shape.keys():
            return member_shape['enum'][0]
        if "min" in member_shape.keys():
            return 'a'*member_shape['min']
        return 'a'

    def _gen_regex_pattern(self, pattern):
        # Some patterns break
        x = Xeger()
        try:
            result = x.xeger(pattern)
            return result
        except:
            return "a"