# coding=utf-8

"""
treblle_flask.telemetry_publisher
~~~~~~~~~~~~~~~~~~~~~~~

This module implements the TelemetryPublisher class, which is responsible for asynchronously
publishing telemetry to Treblle backend.

You shouldn't use this class directly, instead use Treblle class from the extension module.
"""

from aiohttp import ClientSession
from asyncio import new_event_loop, run_coroutine_threadsafe, set_event_loop
from itertools import cycle
from logging import getLogger
from threading import Thread

logger = getLogger('treblle')


class TelemetryPublisher:
    _instance = None
    BACKEND_HOSTS = [
        'https://rocknrolla.treblle.com',
        'https://punisher.treblle.com',
        'https://sicario.treblle.com',
    ]
    TIMEOUT_SECONDS = 2

    def __init__(self, treblle_api_key):
        """
        Asynchronously publishes telemetry to Treblle backend in a round-robin fashion.

        You shouldn't use this class directly, instead use Treblle class from the extension module.
        """

        self._treblle_api_key = treblle_api_key
        self._hosts_cycle = cycle(self.BACKEND_HOSTS)
        self._session = None

        self._event_loop = new_event_loop()
        self._publisher_thread = Thread(target=self._run_event_loop)
        self._publisher_thread.start()

    def _run_event_loop(self):
        set_event_loop(self._event_loop)
        self._event_loop.run_until_complete(self._init_session())
        self._event_loop.run_forever()

    async def _init_session(self):
        self._session = await ClientSession().__aenter__()

    async def _close_session(self):
        if self._session:
            await self._session.__aexit__(None, None, None)
            self._session = None

    async def _process_request(self, payload):
        try:
            await self._session.post(
                url=next(self._hosts_cycle), json=payload, timeout=self.TIMEOUT_SECONDS,
                headers={'X-API-Key': self._treblle_api_key}
            )
        except Exception as e:
            logger.debug(f'Failed to send telemetry: {e.__class__.__name__}{e.args}')

    def send_to_treblle(self, payload):
        run_coroutine_threadsafe(self._process_request(payload), self._event_loop)

    def teardown(self):
        if self._session:
            run_coroutine_threadsafe(self._close_session(), self._event_loop).result()
            self._event_loop.call_soon_threadsafe(self._event_loop.stop)
            self._publisher_thread.join()

    def __del__(self):
        self.teardown()
