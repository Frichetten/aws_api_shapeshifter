import json

import api

DEFAULT_DEF_LOCATION = "./aws-api-definition.json"


def new(definition=DEFAULT_DEF_LOCATION):
    data = __read_api_definition(definition)
    to_return = {}
    for key, service in data.items():
        # Cludgy, but let's make sure it's a v4 service
        if service[list(service.keys())[0]]['metadata']['signatureVersion'] != "v4":
            continue

        to_return[key] = api.API(key, service)

    return to_return

def convert_sts_to_cred_object(credentials):
    return Credentials(
        credentials['AccessKeyId'], 
        credentials['SecretAccessKey'], 
        credentials['SessionToken'])


def __read_api_definition(definition):
    with open(definition, 'r') as r:
        return json.loads(''.join(r.read()))

class Credentials():

    def __init__(self, access_key, secret_key, token):
        self.access_key = access_key
        self.secret_key = secret_key
        self.token = token


