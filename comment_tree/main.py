import asyncio
from collections import defaultdict
import logging
import sys

from aiohttp import web
import aiohttp_debugtoolbar
from aiohttp.web_middlewares import normalize_path_middleware
from aiohttp_debugtoolbar import toolbar_middleware_factory

from comment_tree.utils import config, error_middleware
from comment_tree.utils import WsWaiters
from comment_tree import db
from comment_tree.routes import setup_routes

debug = True

def create_app(loop, argv=None):

    middlewares = [
        normalize_path_middleware(),
        error_middleware
    ]
    # setup application and extensions
    app = web.Application(loop=loop, middlewares=middlewares)

    if debug:
        aiohttp_debugtoolbar.setup(app, intercept_redirects=False)
        app.middlewares.append(toolbar_middleware_factory)

    # load config from yaml file
    app['config'] = config
    # ws waiters
    app['ws_waiters'] = defaultdict(WsWaiters)
    # setup database
    db.setup(app)
    # setup views and routes
    setup_routes(app)
    return app


def main(argv):
    # init logging
    logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.get_event_loop()

    app = create_app(loop, argv)
    web.run_app(app,
                host=app['config'].host,
                port=app['config'].port)


if __name__ == '__main__':
    main(sys.argv[1:])
