from cobald.daemon import service

from uvicorn.config import Config
from uvicorn.server import Server

import asyncio


@service(flavour=asyncio)
class RestService(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    async def run(self):
        config = Config("tardis.rest.app:app", **self.kwargs)
        await Server(config=config).serve()
