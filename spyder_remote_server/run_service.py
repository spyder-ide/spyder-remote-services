import argparse
import sys

import tornado
import asyncio

from spyder_remote_server.services.routes import ROUTES

async def run(port):
    app = tornado.web.Application(ROUTES)
    app.listen(port)
    await asyncio.get_event_loop().create_future()

def main(argv=[]):
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8888)
    args = parser.parse_args(argv)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(args.port))

if __name__ == "__main__":
    main(sys.argv[1:])
