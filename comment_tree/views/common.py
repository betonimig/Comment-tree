from aiohttp import web, log
from comment_tree.dao.tree import CommentsTreeDAO

# log = logging.getLogger('view.tree')


async def index(request):
    request['app'].loop.create_task()
    return web.Response(text='Работает!')


async def get_comments_tree(request):
    """Return comments tree by entity or root comment"""

    comment_id = request.match_info.get('comment_id')
    if comment_id:
        # valitation was in route (\d+)
        comment_id = int(comment_id)
        tree = CommentsTreeDAO.create_by_parent(comment_id)

    else:
        entity_type = request.match_info.get('entity_type')
        if not entity_type:
            return web.HTTPBadRequest(reason="Entity params error!")
        # valitation was in route (\d+)
        entity_id = int(request.match_info.get('entity_id'))
        tree = CommentsTreeDAO.create_by_entity(entity_type, entity_id)

    await tree.fetch(request['conn'])

    return web.json_response(await tree.rows)


async def get_root_comments_by_entity(request):
    try:
        page = int(request.GET.get('page', 1))
    except TypeError:
        log.debug("Page type error")
        return web.HTTPBadRequest()

    entity_type = request.match_info.get('entity_type')
    if not entity_type:
        return web.HTTPBadRequest(reason="Entity params error!")

    # valitation was in route (\d+)
    entity_id = int(request.match_info.get('entity_id'))

    comments = await CommentsTreeDAO.create_by_entity(
        entity_type,
        entity_id,
        only_roots=True
    ).fetch(request['conn'], page=page)
    return web.json_response(await comments.rows)


async def get_comments_by_user(request):
    try:
        user_id = int(request.match_info.get('user_id'))
    except (TypeError, ValueError):
        return web.HTTPBadRequest()

    comments = await CommentsTreeDAO(user_id=user_id).fetch(request['conn'])
    print(1)
    return web.json_response(await comments.rows)
