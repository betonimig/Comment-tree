from aiopg.sa import create_engine
from sqlalchemy.engine.url import URL


def setup(app):
    """Setup the library in aiohttp fashion."""

    app.middlewares.append(db_middleware)
    # create connection to the database
    app.on_startup.append(init_pg)
    # shutdown db connection on exit
    app.on_cleanup.append(close_pg)


async def db_middleware(app, handler):
    """Create db connection for every request"""
    if 'db' not in app:
        raise RuntimeError('Please setup db with db.setup method')

    async def middleware(request):
        async with app['db'].acquire() as conn:
            request['conn'] = conn
            return await handler(request)

    return middleware


def pg_dsn(conf):
    """
    :param conf: settings including connection settings
    :return: DSN url suitable for sqlalchemy and aiopg.
    """
    return str(URL(
        database=conf['database'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        username=conf['user'],
        drivername='postgres',
    ))


async def init_pg(app):
    """Create DB Engine"""
    pg_conf = app['config'].postgres
    app['db'] = await create_engine(
        pg_dsn(pg_conf),
        minsize=pg_conf['minsize'],
        maxsize=pg_conf['maxsize'],
        loop=app.loop
    )
    # оставим на всякий случай - вдруг передумаю
    # pool = await aiopg.create_pool(
    #     host=conf['host'],
    #     database=conf['database'],
    #     user=conf['user'],
    #     password=conf['password'],
    #     port=conf['port'],
    #     minsize=conf['minsize'],
    #     maxsize=conf['maxsize'],
    #     cursor_factory=psycopg2.extras.RealDictCursor,
    #     loop=app.loop
    # )
    # app['db'] = pool


async def close_pg(app):
    app['db'].close()
    await app['db'].wait_closed()
