from collections import abc
import os
import pathlib
import yaml
import json
from difflib import SequenceMatcher
from aiohttp import web, log

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class Config:

    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super(Config, cls).__new__(cls)
            cls.instance.__load__()
        return cls.instance

    def __load__(self):
        """Load yaml config file"""
        self.project_root = pathlib.Path(__file__).parent.parent

        py_env = os.getenv('PY_ENV', 'development')
        if py_env == 'production':
            cfile = "config/production.yaml"
        else:
            cfile = "config/default.yaml"

        cfile = str(self.project_root / cfile)

        with open(cfile, 'r') as ymlfile:
            cfg = yaml.load(ymlfile)

        self.__dict__.update(cfg)


config = Config()


class IncorrectExportFormat(Exception):
    pass


class Exporter:

    def __init__(self, fmt, comments):
        self.comments = comments
        self._fmt = fmt
        try:
            self.export = getattr(self, '_'+fmt)
        except AttributeError:
            raise IncorrectExportFormat()

    async def _xml(self, file_name):
        """Export comments to xml"""
        comments = ET.Element("comments")

        async for comment in self.comments:
            print(dict(comment))
            attrs = {
                'id': str(comment['id']),
                'created_dt': comment['created_dt'],
                'user_id': str(comment['user_id']),
            }
            if comment['parent_id'] is not None:
                attrs['parent_id'] = str(comment['parent_id'])
            ET.SubElement(comments, "comment", attrs).text = comment['text']

        tree = ET.ElementTree(comments)
        file_path = "static/{}.xml".format(file_name)
        tree.write(file_path, encoding="utf-8")
        return file_path


class WsWaiters(abc.AsyncIterator, list):
    """
    [Broadcasting]list that broadcasts str messages for it`s members.
    Exclusively for aiohttp WebSocketResponse instances.
    """
    def __init__(self):
        super(WsWaiters, self).__init__()
        self._list = []

    async def broadcast(self, message):
        log.web_logger.info('Sending message to %d waiters', len(self))
        async for waiter in self:
            try:
                waiter.send_json(message)
            except Exception as e:
                print('error, ', e)

    async def __aiter__(self):
        self._gen = (i for i in self)
        return self

    async def __anext__(self):
        try:
            return next(self._gen)
        except StopIteration:
            raise StopAsyncIteration


def create_diff(a, b):
    """Create diff between a and b for turn a to b on client"""
    diff = []
    if a == b:
        return diff

    if not a:
        return [['insert', 0, 0, b]]

    s = SequenceMatcher(a=a, b=b)
    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'equal':
            continue
        diff.append([tag, i1, i2, b[j1:j2]])

    return diff


def json_error(message):
    return web.Response(
        body=json.dumps({'error': message}).encode('utf-8'),
        content_type='application/json')


async def error_middleware(app, handler):
    async def middleware_handler(request):
        try:
            response = await handler(request)
            if response.status == 400:
                return json_error(response.reason)
            return response
        except web.HTTPException as ex:
            if ex.status == 400:
                return json_error(ex.reason)
            raise
    return middleware_handler
