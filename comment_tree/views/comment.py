from aiohttp import web
import logging

from comment_tree.dao.comment import CommentDAO
from comment_tree.dao.comment import CommentHasChild, DoesNotExists
from comment_tree.dao.comment_hisory import CommentHistoryDAO
from comment_tree.utils import create_diff

log = logging.getLogger('view.comment')


class CommentView(web.View):
    """Defined Comment REST API"""

    def validate_comment_id(self):
        try:
            return int(self.request.match_info.get('comment_id'))
        except ValueError:
            raise web.HTTPBadRequest(reason="Field 'comment_id' should be int")

    def validate_user_id(self, data):
        try:
            return int(data.get('user_id'))
        except (TypeError, ValueError):
            raise web.HTTPBadRequest(reason="Field 'user_id' should be int!")

    async def get(self):
        """Return comment by id"""

        comment_id = self.validate_comment_id()
        comment = await CommentDAO.get_by_id(self.request['conn'], comment_id)
        if comment is None:
            return web.HTTPBadRequest(reason="Comment does not exists!")
        return web.json_response(dict(comment))

    async def post(self):
        """Create comment"""

        data = await self.request.post()
        log.debug('Create comment {}'.format(data))

        user_id = self.validate_user_id(data)

        parent_id = data.get('parent_id')
        if parent_id is not None:
            try:
                parent_id = int(parent_id)
            except (TypeError, ValueError):
                return web.HTTPBadRequest(reason="Field 'parent_id' should be int!")

        entity_type = data.get('entity_type')
        entity_id = data.get('entity_id')

        if not entity_type or not entity_id:
            return web.HTTPBadRequest(reason="Entity params error!")

        text = data.get('text')
        if not text:
            return web.HTTPBadRequest(reason="Field 'text' is missing!")

        conn = self.request['conn']
        async with conn.begin():
            try:
                comment = await CommentDAO(
                    user_id,
                    entity_type,
                    entity_id,
                    text,
                    parent_id=parent_id).save(self.request['conn'])
                await self.actions_to_history(
                    conn, 'insert', comment, user_id)
            except DoesNotExists as e:
                return web.HTTPBadRequest(reason=str(e))

        return web.json_response(dict(comment))

    async def put(self):
        """Update comment"""
        conn = self.request['conn']
        comment_id = self.validate_comment_id()
        data = await self.request.post()
        # editor
        editor_id = self.validate_user_id(data)

        text = data.get('text')
        if text is None or text == '':
            return web.HTTPBadRequest(reason="Field 'text' is missing!")

        comment = await CommentDAO.get_by_id(conn, comment_id)
        if comment is None:
            return web.HTTPBadRequest(reason="Comment does not exists!")

        old_text, comment.text = comment.text, text
        async with conn.begin():
            await comment.save(conn)
            await self.actions_to_history(
                conn, 'update', comment, editor_id, old_text)

        return web.json_response(dict(comment))

    async def delete(self):
        """Delete comment"""
        data = await self.request.post()
        log.debug('Delete comment {}'.format(data))

        conn = self.request['conn']
        comment_id = self.validate_comment_id()
        # editor
        editor_id = self.validate_user_id(data)

        comment = await CommentDAO.get_by_id(conn, comment_id)
        if comment is None:
            return web.HTTPBadRequest(reason="Comment does not exists!")

        async with conn.begin():
            try:
                await comment.delete(conn)
                await self.actions_to_history(
                    conn, 'delete', comment, editor_id)

            except CommentHasChild as e:
                raise web.HTTPBadRequest(reason=str(e))

            except Exception as e:
                log.debug('Delete comment {} - error:{}'.format(comment_id, e))
                print(e)
                raise e

        return web.json_response({'status': 'success'})

    async def actions_to_history(self, conn, action, comment, user_id,
                                 old_text=None):
        """Saves changes comments in the history"""

        diff = None
        if action != 'delete':
            diff = create_diff(old_text, comment.text)

        comment_history = CommentHistoryDAO(conn)
        await comment_history.insert(action, comment.pk, user_id, diff)

        self.request.app.loop.create_task(
            broadcast_modifications(self.request.app, action, comment, diff))
        # await conn.execute("NOTIFY comment_ch, %s", json.dumps(notify))


async def broadcast_modifications(app, action, comment, diff):
    """Sends modifications to the websocket of waiters"""

    entity_key = "{}_{}".format(comment.entity_type, comment.entity_id)
    notify = {'action': action, 'comment': dict(comment), 'diff': diff}
    waiters = app['ws_waiters'].get(entity_key)
    if waiters:
        await waiters.broadcast(notify)


async def ws_handler(request):
    """Websocket notifications handler"""

    entity_type = request.match_info.get('entity_type')
    # valitation was in route (\d+)
    entity_id = int(request.match_info.get('entity_id'))

    if not entity_type or not entity_id:
        return web.HTTPBadRequest(reason="Entity params error!")

    # create ws
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # append to waiters by entity
    entity_key = "{}_{}".format(entity_type, entity_id)
    waiters = request.app['ws_waiters'][entity_key]
    waiters.append(ws)

    log.debug("ws_handler waiters: {}".format(waiters))
    try:
        async for msg in ws:
            # handle incoming messages
            log.info("WS MSG: {}".format(msg))
    except Exception as e:
        log.debug("ws_handler error:{}".format(e))
    finally:
        waiters.remove(ws)
        log.debug("ws_handler waiters: {}".format(waiters))
