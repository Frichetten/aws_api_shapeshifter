import sys, os, base64, datetime, hashlib, hmac 
import requests

from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def _sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

def _getSignatureKey(key, date_stamp, regionName, serviceName):
    kDate = _sign(('AWS4' + key).encode('utf-8'), date_stamp)
    kRegion = _sign(kDate, regionName)
    kService = _sign(kRegion, serviceName)
    kSigning = _sign(kService, 'aws4_request')
    return kSigning

def query_signer(credentials, method, endpoint_prefix, 
                host, region, endpoint, 
                request_uri, formatted_request):

    request_parameters = formatted_request['body']

    t = datetime.datetime.utcnow()
    date_stamp = t.strftime('%Y%m%d')

    canonical_uri = request_uri

    ## Step 3: Create the canonical query string. In this example, request
    # parameters are passed in the body of the request and the query string
    # is blank.
    canonical_querystring = ''

    canonical_headers = _build_canonical_headers(formatted_request['headers'])

    signed_headers = _build_signed_headers(formatted_request['headers'])

    payload_hash = hashlib.sha256(request_parameters.encode('utf-8')).hexdigest()

    canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = date_stamp + '/' + region + '/' + endpoint_prefix + '/' + 'aws4_request'
    string_to_sign = algorithm + '\n' +  formatted_request['headers']['X-Amz-Date'] + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    signing_key = _getSignatureKey(credentials.secret_key, date_stamp, region, endpoint_prefix)

    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

    authorization_header = algorithm + ' ' + 'Credential=' + credentials.access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

    headers = formatted_request['headers']
    headers['Authorization'] = authorization_header

    r = requests.post(endpoint, data=request_parameters, headers=headers, verify=False)
    headers.pop("Authorization")

    return r

def json_signer(access_key, secret_key, token, method, endpoint_prefix, 
                host, region, endpoint, content_type, amz_target, 
                request_uri, request_map):
    service = endpoint_prefix
    host = host
    region = region
    endpoint = endpoint
    content_type = content_type
    amz_target = amz_target

    request_parameters =  '{}'

    access_key = access_key
    secret_key = secret_key
    token = token
    if access_key is None or secret_key is None:
        print('No access key is available.')
        sys.exit()

    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    date_stamp = t.strftime('%Y%m%d')

    canonical_uri = request_uri

    ## Step 3: Create the canonical query string. In this example, request
    # parameters are passed in the body of the request and the query string
    # is blank.
    canonical_querystring = ''

    canonical_headers = 'content-type:' + content_type + '\n' + 'host:' + host + '\n' + 'x-amz-date:' + amz_date + '\n' + 'x-amz-target:' + amz_target + '\n'

    signed_headers = 'content-type;host;x-amz-date;x-amz-target'

    payload_hash = hashlib.sha256(request_parameters.encode('utf-8')).hexdigest()

    canonical_request = method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

    algorithm = 'AWS4-HMAC-SHA256'
    credential_scope = date_stamp + '/' + region + '/' + endpoint_prefix + '/' + 'aws4_request'
    string_to_sign = algorithm + '\n' +  amz_date + '\n' +  credential_scope + '\n' +  hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    signing_key = _getSignatureKey(secret_key, date_stamp, region, endpoint_prefix)

    signature = hmac.new(signing_key, (string_to_sign).encode('utf-8'), hashlib.sha256).hexdigest()

    authorization_header = algorithm + ' ' + 'Credential=' + access_key + '/' + credential_scope + ', ' +  'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

    headers = {'Content-Type':content_type,
            'X-Amz-Date':amz_date,
            'X-Amz-Target':amz_target,
            'X-Amz-Security-Token':token,
            'Authorization':authorization_header}

    r = requests.post(endpoint, data=request_parameters, headers=headers, verify=False)
    return r

def _build_canonical_headers(headers):
    headers_string = ""
    for header in headers.keys():
        headers_string += header.lower() + ":" + headers[header] + "\n"

    return headers_string
 
def _build_signed_headers(headers):
    headers_string = ""
    for header in headers.keys():
        headers_string += header.lower() + ";"
    # Remove trailing ';'
    headers_string = headers_string[:-1]

    return headers_string
