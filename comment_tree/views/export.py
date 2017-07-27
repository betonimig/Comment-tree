import asyncio
from aiohttp import web
from datetime import datetime
import logging
import json
import uuid

from comment_tree.dao.tree import CommentsTreeDAO
from comment_tree.utils import Exporter

log = logging.getLogger('view.export')


async def request_to_export(request):
    """Create request for export comments history by user or
       entity to file"""

    params = {}
    params['format'] = request.GET.get('format', 'xml')
    user_id = request.match_info.get('user_id')
    if user_id:
        try:
            user_id = int(user_id)
            params['user_id'] = user_id
        except ValueError:
            return web.HTTPBadRequest()

    else:
        params['entity_type'] = request.match_info.get('entity_type')
        try:
            params['entity_id'] = int(request.match_info.get('entity_id'))
        except (TypeError, ValueError):
            return web.HTTPBadRequest()

    from_dt = request.GET.get('fdt')
    to_dt = request.GET.get('tdt')
    dt_format = '%Y-%m-%d %H:%M:%S'
    try:
        if from_dt:
            from_dt = datetime.strptime(from_dt, dt_format)
            if to_dt:
                to_dt = datetime.strptime(to_dt, dt_format)
            else:
                to_dt = datetime.now()

            if from_dt > to_dt:
                from_dt, to_dt = to_dt, from_dt

            params.update({'fdt': from_dt, 'tdt': to_dt})
    except ValueError:
        return web.HTTPBadRequest()

    # get uuid for export request id
    req_id = str(uuid.uuid4())
    params['id'] = req_id

    sql = """
        INSERT INTO export_request_tbl
            (id, format, data)
        VALUES
            (%s, %s, %s)"""
    await request['conn'].execute(
        sql,
        *[req_id, params['format'], json.dumps(params, default=str)]
    )

    request.app.loop.create_task(export_to_file_task(request['conn'], params))

    return web.json_response({'req_id': req_id})


async def get_file_by_uuid(request):
    """Return file by export request id"""

    req_id = request.match_info.get('req_id')
    if not req_id:
        return web.HTTPBadRequest()

    # validate req_id
    try:
        uuid.UUID(req_id, version=4)
    except ValueError:
        return web.HTTPBadRequest(
            reason="Request id is not a valid hex code for a UUID.")

    sql = "SELECT file_path FROM export_request_tbl WHERE id=%s"

    attempt = 0
    while attempt < 5:
        row = await (await request['conn'].execute(sql, req_id)).fetchone()
        if row and row['file_path']:
            return web.HTTPFound('/{}'.format(row['file_path']))
        await asyncio.sleep(1)
        attempt += 1

    return web.json_response({'status': 'processing'})


async def export_to_file_task(conn, params):
    """Task wich export comments to file"""

    comments = CommentsTreeDAO(**params)
    comments = await comments.fetch(
        conn,
        fdt=params.get('fdt'),
        tdt=params.get('tdt')
    )
    file_path = await Exporter(params['format'], comments).export(params['id'])
    await conn.execute(
        "update export_request_tbl set file_path=%s where id=%s",
        *[file_path, params['id']]
    )
    print('tochno rabotaet')
