import json

import api

DEFAULT_DEF_LOCATION = "./aws-api-definition.json"

class aws_api_shapeshifter():

    def __init__(self, definition=DEFAULT_DEF_LOCATION):
        data = self.__read_api_definition(definition)

            # apis[service].latest


    def __read_api_definition(self, definition):
        with open(definition, 'r') as r:
            return json.loads(''.join(r.read()))