from xeger import Xeger

import api_signer
import protocol_formatter
import aws_api_shapeshifter

""" The operation_obj will be the primary location where parameters are altered and configured.
    Every user generated modification will pass throug here. As a result this code is ugly and I'm
    only partially sorry. """
class Operation:

    def __init__(self, metadata, endpoints, shapes, operation):
        self.name = operation['name']
        self.method = operation['http']['method']
        self.request_uri = operation['http']['requestUri']
        self.endpoints = endpoints['endpoints']
        self.metadata = metadata
        self.input_format = self._parse_input_shape(self.metadata['endpointPrefix'], shapes, operation)
        self.endpoint_prefix = metadata['endpointPrefix']
        self.target_prefix = self._resolve_target_prefix(self.metadata)
        self.shape_input = self._resolve_shape_input(operation)

    
    # make_request will take the requested modifications (if any) and make the request to the AWS API
    def make_request(self, **kwargs):
        name = self.name
        version = self.metadata['apiVersion']
        credentials = _resolve_credentials(kwargs)
        endpoint_prefix = self._resolve_endpoint_prefix(kwargs)
        method = self._resolve_method(kwargs)
        region = self._resolve_region(kwargs)
        host = self._resolve_host(region, endpoint_prefix, kwargs)
        endpoint = self._resolve_endpoint(host, kwargs)
        request_uri = self._resolve_request_uri(kwargs)

        if 'noparam' in kwargs.keys() or 'noparams' in kwargs.keys():
            self.input_format = ""

        # Depending on the protocol we need to format inputs differently
        if self.metadata['protocol'] == "query":
            formatted_request = protocol_formatter.query_protocol_formatter(
                host,
                credentials.token,
                name,
                version,
                self.input_format
            )
            response = api_signer.query_signer(
                credentials,
                method,
                endpoint_prefix,
                host,
                region,
                endpoint,
                request_uri,
                formatted_request
            )
            return response

        if self.metadata['protocol'] == "jsonfefe":
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


        return "a"
        

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


    def _resolve_endpoint_prefix(self, kwargs):
        if 'endpoint_prefix' in kwargs.keys():
            return kwargs['endpoint_prefix']

        return self.endpoint_prefix

    
    def _resolve_method(self, kwargs):
        if 'method' in kwargs.keys():
            return kwargs['method']
        
        return self.method


    def _resolve_region(self, kwargs):
        if 'region' in kwargs.keys():
            return kwargs['method']
        
        # ngl, gonna prefer us-east-1
        if 'us-east-1' in self.endpoints.keys():
            return 'us-east-1'
        
        # Otherwise, pick a random region that they support
        # Need to check for a credential scope region
        potential = list(self.endpoints.keys())[0]
        if "credentialScope" in self.endpoints[potential].keys():
            return self.endpoints[potential]['credentialScope']['region']
        
        return potential


    def _resolve_host(self, region, endpoint_prefix, kwargs):
        if 'host' in kwargs.keys():
            return kwargs['host']

        # iam is an example of this - Need to check for a hostname for a region
        # not in the keys (aws-global)
        potential = list(self.endpoints.keys())[0]
        if region == self.endpoints[potential]['credentialScope']['region']:
            return self.endpoints[potential]['hostname']

        if 'hostname' in self.endpoints[region].keys():
            return self.endpoints[region]['hostname'] 
        
        # I know this is broken but will wait to fix until I have 
        # more examples
        return endpoint_prefix + "." + region + ".amazonaws.com"

    
    def _resolve_endpoint(self, host, kwargs):
        if 'endpoint' in kwargs.keys():
            return kwargs['endpoint']

        return "https://" + host

    
    def _resolve_request_uri(self, kwargs):
        if 'request_uri' in kwargs.keys():
            return kwargs['request_uri']

        return self.request_uri


    def _resolve_target_prefix(self, metadata):
        if 'targetPrefix' in metadata.keys(): 
            return metadata['targetPrefix']
        else:
            return metadata['endpointPrefix']


    def _resolve_shape_input(self, operation):
        if 'input' in operation.keys():
            return operation['input']['shape']
        return ""


    # GIVE THIS THE SHAPE, NOT THE NAME
    def _resolve_unknown_shape(self, shapes, unknown_shape, component_name):
        unknown_shape_type = unknown_shape['type']
        if unknown_shape_type == 'string':
            return self._gen_string_shape(unknown_shape, component_name)
        if unknown_shape_type == 'integer':
            return (component_name, 1)
        if unknown_shape_type == 'boolean':
            return (component_name, "false")
        if unknown_shape_type == 'structure':
            return self._resolve_structure(shapes, unknown_shape, component_name)
        if unknown_shape_type == 'list':
            return self._resolve_list(shapes, unknown_shape, component_name)
        if unknown_shape_type == 'timestamp':
            return self._resolve_timestamp(shapes, unknown_shape, component_name)
        if unknown_shape_type == 'blob':
            return self._resolve_blob(shapes, unknown_shape, component_name)
        if unknown_shape_type == 'long':
            return (component_name, 1)
        if unknown_shape_type == 'map':
            return (component_name, "map")
        if unknown_shape_type == 'double' or unknown_shape_type == 'float':
            return (component_name, 2.0)
        # Map not implemented -Xray
        print(unknown_shape_type)


    def _resolve_structure(self, shapes, structure, component_name):
        to_return = []
        for member in structure['members']:
            if 'required' in structure.keys() and member in structure['required']:
                shape_name = structure['members'][member]['shape']
                recurse_name = (component_name + "." + member + ".").strip('.')
                to_return.append(self._resolve_unknown_shape(shapes, shapes[shape_name], recurse_name))
        return to_return


    def _resolve_list(self, shapes, list_shape, component_name):
        member_shape = list_shape['member']['shape']
        if 'locationName' in list_shape['member'].keys():
            location_name = list_shape['member']['locationName']
        else:
            # Learned from elasticache RemoveTagsFromResource
            location_name = 'member'
        recurse_name = (component_name + "." + location_name).strip('.')
        result = self._resolve_unknown_shape(shapes, shapes[member_shape], recurse_name)
        return result


    def _resolve_timestamp(self, shapes, timestamp, component_name):
        return (component_name, "1615593755.796672")


    def _resolve_blob(self, shapes, blob, component_name):
        return ("bbbbbbbbebfbebebbebebb")
 

    def _parse_input_shape(self, name, shapes, operation):
        to_return = {}

        # Not every operation has an input
        if 'input' in operation.keys():
            input_shape_name = operation['input']['shape']
            shape = shapes[input_shape_name]
             
            if "required" in shape.keys():
                # This is actual torture
                # TODO: Refactor
                result = self._resolve_unknown_shape(shapes, shape, "")
                values = [f for f in self._flatten_list(result)]
                i = 2
                for item in values:
                    if "." in item[0]:
                        if "Key" in item[0]:
                            new_name = item[0] + "." + str(i//2)
                            new_name = new_name.replace(".Key.",".") + ".Key"
                        elif "Value" in item[0]:
                            new_name = item[0] + "." + str(i//2)
                            new_name = item[0].replace(".Value.", ".") + ".Value"
                        else:
                            new_name = item[0] + "." + str(i//2)
                        i += 1
                        to_return[new_name] = item[1]
                    else:
                        to_return[item[0]] = item[1]

                return to_return

        return ""


    def _flatten_list(self, list_in):
        if isinstance(list_in, list):
            for l in list_in:
                for y in self._flatten_list(l):
                    yield y

        else:
            yield list_in


    def _gen_string_shape(self, member_shape, component_name):
        # min, max, pattern, enum
        if "pattern" in member_shape.keys():
            return (component_name, self._gen_regex_pattern(member_shape['pattern']))
        if "enum" in member_shape.keys():
            return (component_name, member_shape['enum'][0])
        if "min" in member_shape.keys():
            return (component_name, 'a'*member_shape['min'])
        return (component_name, 'aaaaaa')


    def _gen_regex_pattern(self, pattern):
        # Some patterns break
        x = Xeger()
        try:
            result = x.xeger(pattern)
            return result
        except:
            return "a"


def _resolve_credentials(kwargs):
    """ A user can send a few types of creds at us, and we 
        have to be able to resolve them. Output should 
        always be a credential object with .access_key, 
        .secret_key, and .token accessible """
    kwargs_keys = kwargs.keys()
    # Assume that access key modification is intentional and 
    # is a higher priority
    if 'access_key' in kwargs_keys:
        return aws_api_shapeshifter.Credentials(
            kwargs['access_key'],
            kwargs['secret_key'],
            kwargs['token']
        )

    elif 'creds' in kwargs_keys:
        return kwargs['creds']

    elif 'credentials' in kwargs_keys:
        return kwargs['credentials']
    
    return aws_api_shapeshifter.Credentials("", "", "")


def _resolve_region_hostname(endpoints, preferred=''):
    # If there is a hostname return in
    # otherwise just return the region
    None