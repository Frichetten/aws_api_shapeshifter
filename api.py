import boto3
import socket

import api_signer

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

    def __init__(self, key, service):
        self._definition = service
        self._latest_version = self.latest_version()
        self.protocol = self.latest()['metadata']['protocol']
        self.operations = self._make_operations_list(self.latest()['metadata'], self.latest()['endpoints'], self.latest()['operations'])
        self.endpoints = self.latest()['endpoints']

    # Returns the definiton of the lastest api version
    def latest(self):
        # Find the most recent api version
        # We can do this by sorting keys
        options = list(self._definition.keys())
        options.sort()
        return self._definition[options[0]]

    def latest_version(self):
        return list(self._definition.keys())[0]

    # Returns a list of the available API versions
    def api_versions(self):
        return list(self._definition.keys())

    def _make_operations_list(self, metadata, endpoints, operations):
        to_return = {}
        for operation, details in operations.items():
            to_return[operation] = Operation(metadata, endpoints, details)

        return to_return
            

class Operation:

    def __init__(self, metadata, endpoints, details):
        self.name = details['name']
        self.method = details['http']['method']
        self.request_uri = details['http']['requestUri']
        self.endpoints = endpoints

        self.endpoint_prefix = metadata['endpointPrefix']

        if 'targetPrefix' in metadata.keys(): 
            self.target_prefix = metadata['targetPrefix']
        else:
            self.target_prefix = metadata['endpointPrefix']

        # Not ever API has these fields
        if 'input' in details.keys():
            self.input = details['input']['shape']
            
        if 'output' in details.keys():
            self.output = details['output']['shape']

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
        request_uri=''
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
            request_uri=request_uri
        )

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