
from comment_tree.views.comment import CommentView, ws_handler
from comment_tree.views import common, export, comment_history


def setup_routes(app):
    app.router.add_get('/', common.index)

    # API for comment: GET, POST, PUT, DELETE
    app.router.add_route('*', '/comment/{comment_id:\d*}', CommentView)
    # notifications about comment modifications
    app.router.add_get('/comment/ws/{entity_type}/{entity_id:\d+}/', ws_handler)

    app.router.add_get('/comment/history/{comment_id:\d+}/',
                       comment_history.get_history_by_comment)

    # Comments tree:
    # by comment id
    app.router.add_get('/tree/{comment_id:\d+}/', common.get_comments_tree)
    # by entity
    app.router.add_get('/tree/{entity_type}/{entity_id:\d+}/', common.get_comments_tree)

    # root comments by entity
    app.router.add_get('/comments/{entity_type}/{entity_id:\d+}/',
                       common.get_root_comments_by_entity)
    # comemnts by user
    app.router.add_get('/comments/{user_id:\d+}/', common.get_comments_by_user)

    # Export:
    # create request for export by user or entity
    app.router.add_get('/export/request/{user_id:\d+}/', export.request_to_export)
    app.router.add_get('/export/request/{entity_type}/{entity_id:\d+}/',
                       export.request_to_export)
    # check export status and redirect to download file
    app.router.add_get('/export/file/{req_id}/', export.get_file_by_uuid)

    # static
    app.router.add_static('/static/',
                          path=str(app['config'].project_root / 'static'))
