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


def __read_api_definition(definition):
    with open(definition, 'r') as r:
        return json.loads(''.join(r.read()))
