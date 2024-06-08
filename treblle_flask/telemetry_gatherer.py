# coding=utf-8

"""
treblle_flask.telemetry_gatherer
~~~~~~~~~~~~~~~~~~~~~~~

This module implements the TelemetryGatherer class, which is responsible for gathering telemetry data
about the server, request and response objects, and any unhandled errors which occured during the requests.
It generates a payload to send to Treblle backend.

You shouldn't use this class directly, instead use Treblle class from the extension module.
"""

from copy import deepcopy
from datetime import datetime, timezone
from flask import request, g
from json import JSONDecodeError, dumps, loads
from logging import getLogger
from platform import python_version, system, release, machine
from socket import getaddrinfo, gethostname, AF_INET
from time import time
from traceback import extract_tb
from types import GeneratorType

logger = getLogger('treblle')


class TelemetryGatherer:
    # Common authentication schemes, if authorization header starts with one of these strings, we'll mask the value,
    # but keep the scheme visible. Otherwise, we'll mask the entire header to be safe.
    COMMON_AUTH_SCHEMES = {'Basic', 'Bearer', 'Digest', 'Negotiate', 'OAuth', 'AWS4-HMAC-SHA256', 'HOBA', 'Mutual'}

    def __init__(
        self, treblle_api_key, treblle_project_id, hidden_keys, mask_auth_header, limit_request_body_size,
        request_transformer, response_transformer
    ):
        """
        Gathers telemetry data about the server, request and response objects, and any unhandled errors which occured
        during the requests and generates a payload to send to Treblle backend.

        You shouldn't use this class directly, instead use Treblle class from the extension module.
        """

        self._hidden_keys = hidden_keys
        self._should_mask_auth_header = mask_auth_header
        self._limit_request_body_size = limit_request_body_size
        self._request_transformer = request_transformer
        self._response_transformer = response_transformer
        self._disabled = not treblle_api_key or not treblle_project_id

        try:
            addrinfo = getaddrinfo(gethostname(), None)
            host_ip = [host for family, *_, host in addrinfo if family == AF_INET][0][0]
        except (OSError, IndexError):
            host_ip = 'unknown'

        self._payload_template = {
            'api_key': treblle_api_key, 'project_id': treblle_project_id,
            'sdk': 'flask', 'version': 0.6,
            'data': {
                'server': {
                    'ip': host_ip,
                    'timezone': datetime.now(timezone.utc).astimezone().tzinfo.tzname(None),
                    'os': {'name': system(), 'release': release(), 'architecture': machine()},
                },
                'language': {'name': 'python', 'version': python_version()},
                'errors': []
            }
        }

    def _mask_data(self, data):
        if not self._hidden_keys:
            return data

        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if key in self._hidden_keys:
                    masked_data[key] = '*'*len(str(value))
                else:
                    masked_data[key] = self._mask_data(value)
            return masked_data

        elif isinstance(data, list):
            return [self._mask_data(item) for item in data]

        return data

    def _mask_auth_header(self, auth_header):
        if ' ' not in auth_header:
            return '*'*len(auth_header)  # likely malformed, just mask the entire header

        auth_scheme, auth_value = auth_header.split(' ', maxsplit=1)
        if auth_scheme in self.COMMON_AUTH_SCHEMES:
            return f'{auth_scheme} {"*"*len(auth_value)}'

        return '*'*len(auth_header)

    def handle_request(self):
        if self._disabled:
            return

        payload = deepcopy(self._payload_template)

        software = request.environ.get('SERVER_SOFTWARE', '')
        protocol = request.environ.get('SERVER_PROTOCOL', '')
        if software.count('/') == 1:
            software, signature = software.split('/')
        else:
            signature = ''
        payload['data']['server'].update({'software': software, 'protocol': protocol, 'signature': signature})

        request_headers = self._mask_data(dict(request.headers))
        if self._should_mask_auth_header and 'Authorization' in request_headers:
            request_headers['Authorization'] = self._mask_auth_header(request_headers['Authorization'])

        x_forwarded_for = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
        request_ip = x_forwarded_for or request.remote_addr

        payload['data']['request'] = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'method': request.method,
            'url': request.url,
            'user_agent': request.user_agent.string,
            'headers': request_headers,
            'ip': request_ip,
        }

        # if the client is acting maliciously, they can still exhaust the server memory by not providing a
        # content-length header or setting transfer-encoding header to chunked, this is a best-effort mitigation,
        # there should be other mechanisms in place to prevent this in production environments
        if (request.content_length or 0) < self._limit_request_body_size:
            if self._request_transformer:
                try:
                    request_body = self._request_transformer(request.get_data())
                    try:
                        dumps(request_body)
                    except JSONDecodeError:
                        raise ValueError('Request transformer must return a JSON serializable object')

                except Exception as e:
                    logger.error(f'Error in request transformer: {e.__class__.__name__}{e.args}')
                    last_frame = extract_tb(e.__traceback__)[-1]
                    payload['data']['errors'].append({
                        'source': 'onError',
                        'type': e.__class__.__name__,
                        'message': ', '.join(str(f) for f in e.args),
                        'file': last_frame.filename,
                        'line': last_frame.lineno
                    })
                    request_body = {}

            else:
                try:
                    request_body = loads(request.get_data().decode('utf-8', 'replace'))
                except JSONDecodeError:
                    request_body = {}

            payload['data']['request']['body'] = self._mask_data(request_body)

        g.treblle_payload = payload
        g.treblle_start_time = time()

    def handle_response(self, response):
        if self._disabled:
            return response

        response_headers = self._mask_data(dict(response.headers))

        payload = g.treblle_payload
        payload['data']['response'] = {
            'code': response.status_code,
            'headers': response_headers,
            'load_time': time()-g.treblle_start_time,
        }

        if isinstance(response.response, GeneratorType):
            # streaming response - we don't want to block the request thread to wait for the response to finish
            # or load the entire response into memory
            payload['data']['response'].update({'size': 0, 'body': {}})
        else:
            if self._response_transformer:
                try:
                    response_body = self._response_transformer(response.data)
                    try:
                        dumps(response_body)
                    except JSONDecodeError:
                        raise ValueError('Response transformer must return a JSON serializable object')

                except Exception as e:
                    logger.error(f'Error in response transformer: {e.__class__.__name__}{e.args}')
                    last_frame = extract_tb(e.__traceback__)[-1]
                    payload['data']['errors'].append({
                        'source': 'onError',
                        'type': e.__class__.__name__,
                        'message': ', '.join(str(f) for f in e.args),
                        'file': last_frame.filename,
                        'line': last_frame.lineno
                    })
                    response_body = {}

            else:
                try:
                    response_body = loads(response.data.decode('utf-8', 'replace'))
                except (JSONDecodeError, UnicodeDecodeError):
                    response_body = {}

            payload['data']['response']['body'] = self._mask_data(response_body)
            payload['data']['response']['size'] = len(response.data)

        return response

    def finalize(self, exception):
        if self._disabled or not hasattr(g, 'treblle_payload'):
            return

        if exception:
            # treblle doesn't support entire traceback, we'll only send the last frame
            last_frame = extract_tb(exception.__traceback__)[-1]

            g.treblle_payload['data']['errors'].append({
                'source': 'onError',
                'type': exception.__class__.__name__,
                'message': ', '.join(str(f) for f in exception.args),
                'file': last_frame.filename,
                'line': last_frame.lineno
            })

        return g.treblle_payload
