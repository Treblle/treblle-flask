# coding=utf-8

"""
treblle_flask.extension
~~~~~~~~~~~~~~~~~~~~~~~

This module implements the Treblle Flask extension, allowing you to easily
integrate Treblle into your Flask application.
"""

from atexit import register as atexit_register
from signal import signal, SIGINT
from logging import getLogger
from os import environ
from typing import Iterable, Optional, Callable, Union
from treblle_flask.telemetry_gatherer import TelemetryGatherer
from treblle_flask.telemetry_publisher import TelemetryPublisher

logger = getLogger('treblle')
__all__ = ['Treblle']


class Treblle:
    DEFAULT_HIDDEN_KEYS = [
        'password', 'pwd', 'secret', 'password_confirmation',
        'passwordConfirmation', 'cc', 'card_number', 'cardNumber', 'ccv',
        'ssn', 'credit_score', 'creditScore', 'authorization'
    ]
    DEFAULT_LIMIT_REQUEST_BODY_SIZE = 4*1024*1024

    def __init__(
        self, app=None, *,
        TREBLLE_API_KEY: str = None,
        TREBLLE_PROJECT_ID: str = None,
        hidden_keys: Optional[Iterable[str]] = None,
        mask_auth_header: bool = True,
        limit_request_body_size: Optional[int] = None,
        request_transformer: Optional[Callable[[bytes], Union[dict, list, str, int, float]]] = None,
        response_transformer: Optional[Callable[[bytes], Union[dict, list, str, int, float]]] = None
    ):
        """
        The Treblle extension entry point. Configures the extensions with the given Flask app.

        Uses environment variables to configure the extension. If you want to override the default configuration,
        you can pass a dictionary of options to the constructor.

        :param app: The Flask application to configure.
        :param TREBLLE_API_KEY: The API key, also available as an environment variable.
        :param TREBLLE_PROJECT_ID: The project ID, also available as an environment variable.
        :param hidden_keys: A list of keys to mask in the request/response body/header payloads.
         Uses a default list if not set. To prevent masking, set to empty list or set
        :param mask_auth_header: A boolean flag whether to mask the Authorization header on request. Masking will
         retain the header directive but replace the secret value with asterisks.
        :param limit_request_body_size: The maximum size of the request body to capture. Uses a default value if unset.
         Set to 0 to disable request body capturing. If request doesn't include content-length header, the body will be
         captured regardless of the size.
        :param request_transformer: A function to transform the request body before sending it to Treblle.
        :param response_transformer: A function to transform the response body before sending it to Treblle.
        """

        if TREBLLE_API_KEY and environ.get('TREBLLE_API_KEY'):
            logger.warning('TREBLLE_API_KEY is set both as a keyword argument and environment variable!')
        self._treblle_api_key = TREBLLE_API_KEY or environ.get('TREBLLE_API_KEY')

        if TREBLLE_PROJECT_ID and environ.get('TREBLLE_PROJECT_ID'):
            logger.warning('TREBLLE_PROJECT_ID is set both as a keyword argument and environment variable!')
        self._treblle_project_id = TREBLLE_PROJECT_ID or environ.get('TREBLLE_PROJECT_ID')

        if hidden_keys is not None:
            self._hidden_keys = set(hidden_keys)
        else:
            self._hidden_keys = Treblle.DEFAULT_HIDDEN_KEYS
        self._mask_auth_header = bool(mask_auth_header)

        if limit_request_body_size is not None:
            self._limit_request_body_size = limit_request_body_size
        else:
            self._limit_request_body_size = Treblle.DEFAULT_LIMIT_REQUEST_BODY_SIZE

        self._request_transformer = request_transformer
        self._response_transformer = response_transformer
        self._telemetry_gatherer = self._telemetry_publisher = None

        app.before_request(self._handle_request)
        app.after_request(self._handle_response)
        app.teardown_request(self._teardown_request)
        atexit_register(self._teardown)
        signal(SIGINT, self._teardown)

    def _handle_request(self):
        if self._telemetry_publisher is None:
            if not self._treblle_api_key or not self._treblle_project_id:
                logger.error(
                    f'\n\nTreblle Flask extension is not properly configured - '
                    f'API key and project ID are required!\n\n'
                    f'Set TREBLLE_API_KEY and TREBLLE_PROJECT_ID environment variables\n'
                    f'or pass them as kwargs when initializing in your Flask application:\n\n'
                    f'    app = Flask(__name__)\n'
                    f'    Treblle(app, TREBLLE_API_KEY="your-api-key", TREBLLE_PROJECT_ID="your-project-id")\n\n'
                    f'For more information, visit https://docs.treblle.com/integrations/python/flask/\n\n'
                )

            self._telemetry_gatherer = TelemetryGatherer(
                self._treblle_api_key, self._treblle_project_id, self._hidden_keys, self._mask_auth_header,
                self._limit_request_body_size, self._request_transformer, self._response_transformer
            )
            self._telemetry_publisher = TelemetryPublisher(self._treblle_api_key)

        self._telemetry_gatherer.handle_request()

    def _handle_response(self, response):
        return self._telemetry_gatherer.handle_response(response)

    def _teardown_request(self, exception=None):
        payload = self._telemetry_gatherer.finalize(exception)
        if payload:
            self._telemetry_publisher.send_to_treblle(payload)
        return exception

    def _teardown(self, *_args):
        if self._telemetry_publisher:
            self._telemetry_publisher.teardown()


if __name__ == '__main__':
    logger.warning('This is a Flask extension. It is not meant to be run directly.')
