from aiohttp import web

from comment_tree.dao.comment_hisory import CommentHistoryDAO


async def get_history_by_comment(request):
    """Return history of comment"""
    try:
        comment_id = int(request.match_info.get('comment_id'))
    except ValueError:
        raise web.HTTPBadRequest(reason="Field 'comment_id' should be int")

    rows = await CommentHistoryDAO(request['conn']).get_by_comment(comment_id)
    return web.json_response(rows)
