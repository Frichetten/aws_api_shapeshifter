import datetime

from urllib.parse import urlencode

ALL_DEFAULT_HEADERS = {
    'Host': '',
    'X-Amz-Date': '',
    'X-Amz-Security-Token': '',
}

QUERY_DEFAULT_HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
}

def query_protocol_formatter(host, token, name, version, input_format, headers=''):
    gathered_headers = _resolve_headers(headers, QUERY_DEFAULT_HEADERS)
    complete_headers = _complete_headers(gathered_headers, host, token)
    to_return = { 'headers' : complete_headers }

    # TODO: Factor in the shape to create body params
    # Currently only handling strings
    body_map = { 'Action': name }
    body_map['Version'] = version 
    body_map.update(input_format)
    to_return['body'] = urlencode(body_map)

    return to_return

def _resolve_headers(custom_headers, default_headers):
    if custom_headers == '':
        default_headers.update(ALL_DEFAULT_HEADERS)
        return default_headers
    else:
        return _apply_custom_headers(custom_headers, default_headers)

def _apply_custom_headers(custom_headers, default_headers):
    """ A user may apply a custom header for their request. These will be
    appended to the default headers. """
    to_return = default_headers
    to_return.update(custom_headers)
    to_return.update(ALL_DEFAULT_HEADERS)

    return to_return

def _complete_headers(headers, host, token):
    """ We need to fill in those headers with the info we have """
    for header in headers.keys():
        if header == 'X-Amz-Date':
            headers[header] = _get_date_string()
        if header == 'Host':
            headers[header] = host
        if header == 'X-Amz-Security-Token':
            headers[header] = token

    return headers

def _get_date_string():
    t = datetime.datetime.utcnow()
    amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    return amz_date