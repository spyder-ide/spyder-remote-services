import argparse

import tornado
import asyncio

from spyder_remote_server.app.routes import ROUTES


async def main(port):
    app = tornado.web.Application(ROUTES)
    app.listen(port)
    await asyncio.get_event_loop().create_future()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.port))
