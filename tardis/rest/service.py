from cobald.daemon import service

from uvicorn.config import Config
from uvicorn.server import Server

from functools import lru_cache
import asyncio


@service(flavour=asyncio)
class RestService(object):
    def __init__(self, secrets=None, **fast_api_args):
        self._secrets = secrets or {}
        self._config = Config("tardis.rest.app:app", **fast_api_args)

    @property
    @lru_cache(maxsize=16)
    def secrets(self):
        return self._secrets

    async def run(self):
        await Server(config=self._config).serve()
