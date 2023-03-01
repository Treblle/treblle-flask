# -*- coding: utf-8 -*-
"""
treblle_flask.extension
~~~~~~~~~~~~~~~~~~~~~~~

This module implements the Treblle Flask extension, allowing you to easily
integrate Treblle into your Flask application.
"""
import time
import datetime
from flask import request
import platform
import os
import socket
import json
import requests
import threading


class Treblle(object):
    """
	Initialize the Treblle extension and configure it with the given
	application.

	It uses environment variables to configure the extension. If you want to
	override the default configuration, you can pass a dictionary of options
	to the constructor.

	:param app: The Flask application to configure.
	"""

    def __init__(self, app=None, **kwargs):
        self._options = kwargs
        if app is not None:
            self.init_app(app, **kwargs)

        self.start_time = ''
        self.end_time = ''
        self.hidden_json_keys = [
            "password", "pwd", "secret", "password_confirmation",
            "passwordConfirmation", "cc", "card_number", "cardNumber", "ccv",
            "ssn", "credit_score", "creditScore"
        ]

        # Treblle API
        self.treblle_api_key = os.environ.get('TREBLLE_API_KEY', None) or \
                                 self._options.get('TREBLLE_API_KEY', None)
        self.treblle_project_id = os.environ.get('TREBLLE_PROJECT_ID', '') or \
                                    self._options.get('TREBLLE_PROJECT_ID', '')

        if not self.treblle_api_key or not self.treblle_project_id:
            raise Exception('Treblle API key and project ID are required.')

        self.final_result = {
            "api_key": self.treblle_api_key,
            "project_id": self.treblle_project_id,
            "version": 0.6,
            "sdk": "flask",
            "data": {
                "server": {
                    "ip": "",
                    "timezone": "",
                    "software": "",
                    "signature": "",
                    "protocol": "",
                    "os": {
                        "name": "",
                        "release": "",
                        "architecture": ""
                    }
                },
                "language": {
                    "name": "python",
                    "version": "",
                },
                "request": {
                    "timestamp": "",
                    "ip": "",
                    "url": "",
                    "user_agent": "",
                    "method": "",
                    "headers": {},
                    "body": {}
                },
                "response": {
                    "headers": {},
                    "code": "",
                    "size": "",
                    "load_time": "",
                    "body": {}
                },
                "errors": []
            }
        }

    def init_app(self, app, **kwargs):
        """
		Initialize the Treblle extension with the given application.

		:param app: The Flask application to configure.
		"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_request(self.teardown_request)

    def before_request(self):
        self.start_time = time.time()
        self.final_result['data']['request'][
            'timestamp'] = datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S')

        hostname = socket.gethostname()
        try:
            host_ip = socket.gethostbyname(hostname)
        except Exception as e:
            host_ip = 'unknown'
        self.final_result['data']['server']['ip'] = host_ip
        self.final_result['data']['server'][
            'timezone'] = datetime.datetime.now().strftime('%Z')
        self.final_result['data']['request']['method'] = request.method
        self.final_result['data']['server']['software'] = request.environ.get(
            'SERVER_SOFTWARE', 'SERVER_SOFTWARE_NOT_FOUND')
        self.final_result['data']['server']['protocol'] = request.environ.get(
            'SERVER_PROTOCOL', 'SERVER_PROTOCOL_NOT_FOUND')
        self.final_result['data']['language']['version'] = '.'.join(
            platform.python_version_tuple())
        self.final_result['data']['server']['os']['name'] = platform.system()
        self.final_result['data']['server']['os'][
            'release'] = platform.release()
        self.final_result['data']['server']['os'][
            'architecture'] = platform.machine()
        self.final_result['data']['request']['url'] = request.url
        self.final_result['data']['request'][
            'user_agent'] = request.user_agent.string

        x_forwarded_for = request.headers.getlist("X-Forwarded-For")
        if x_forwarded_for:
            self.final_result['data']['request']['ip'] = x_forwarded_for[0]
        else:
            self.final_result['data']['request']['ip'] = request.remote_addr

        if request.headers:
            self.final_result['data']['request']['headers'] = dict(
                request.headers)

        request_body = request.get_data(cache=False, as_text=True)
        if request_body:
            try:
                request_body = request_body.decode('utf-8')
                request_body = json.loads(request_body)
                print(request_body)
                for key in self.hidden_json_keys:
                    if key in request_body:
                        request_body[key] = '*' * len(request_body[key])
                self.final_result['data']['request']['body'] = request_body
            except Exception as e:
                self.final_result['data']['request']['body'] = request_body

    def after_request(self, response):
        self.final_result['data']['response']['code'] = response.status_code
        self.final_result['data']['response']['headers'] = dict(
            response.headers)
        # Try to give it in dict if possible
        self.final_result['data']['response']['body'] = response.data.decode(
            'utf-8')
        try:
            # No backslash escape
            json_data = json.loads(response.data.decode('utf-8', 'ignore'))
            for key in self.hidden_json_keys:
                if key in json_data:
                    json_data[key] = '*' * len(json_data[key])
            self.final_result['data']['response']['body'] = json_data

        except Exception as e:
            pass

        self.final_result['data']['response']['size'] = response.content_length
        self.final_result['data']['response']['load_time'] = time.time(
        ) - self.start_time

        return response

    def teardown_request(self, exception):
        if exception:
            self.final_result['data']['errors'].append(str(exception))

        thread = threading.Thread(target=self.send_to_treblle)
        thread.start()

        return exception

    def send_to_treblle(self):
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': self.treblle_api_key
        }
        treblle_request = requests.post("https://rocknrolla.treblle.com/",
                                        json=self.final_result,
                                        headers=headers,
                                        timeout=2)
        print(treblle_request.status_code)


if __name__ == "__main__":
    print("This is a Flask extension. It is not meant to be run directly.")