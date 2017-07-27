import logging

from .comment import CommentDAO
from comment_tree.utils import config

log = logging.getLogger('dao.manager')


class CommentsTreeDAO:
    """Class to handle data accessing of comment tree"""
    def __init__(self, entity_type=None, entity_id=None, root_id=None,
                 user_id=None, only_roots=False, **kwargs):

        self._entity_type = entity_type
        self._entity_id = entity_id
        self._root_id = root_id
        self._user_id = user_id
        self._only_roots = only_roots
        self._rows = []

    @staticmethod
    def create_by_parent(parent_id):
        """Create object by parent comment id
        Args:
            parent_id (int): Parent comment id"""
        return CommentsTreeDAO(root_id=parent_id)

    @staticmethod
    def create_by_entity(entity_type, entity_id, only_roots=False):
        """Create object by entity
        Args:
            entity_type (string): Entity type
            entity_id (int): Entity id
            only_roots (bool): Get only root comments"""

        return CommentsTreeDAO(entity_type=entity_type, entity_id=entity_id,
                               only_roots=only_roots)

    async def fetch(self, conn, page=None, fdt=None, tdt=None):
        """Create and execute sql"""

        sql = """SELECT
                    comm.id,
                    to_json(created_dt) as created_dt,
                    entity_type,
                    entity_id,
                    user_id,
                    u.username,
                    text,
                    parent_id,
                    nlevel(ltree_path) as level
                FROM comments_tbl comm, users_tbl u
                WHERE comm.user_id=u.id AND"""
        where = ""
        params = []

        if self._root_id is not None:
            root = await CommentDAO.get_by_id(conn, self._root_id)
            where += " ltree_path <@ %s"
            params.append(root.path)

        if self._entity_type is not None and self._entity_id is not None:
            if where:
                where += " AND"
            where += " entity_type=%s AND entity_id=%s"
            params.extend([self._entity_type, self._entity_id])

        if self._user_id is not None:
            if where:
                where += " AND"
            where += " user_id=%s"
            params.append(self._user_id)

        if not where:
            raise Exception("Sql params error")

        if fdt and tdt:
            where += " AND created_dt between %s and %s"
            params.extend([fdt, tdt])

        if self._only_roots:
            where += " AND parent_id IS NULL"

        if page and where:
            where += " LIMIT %s OFFSET %s"
            limit = config.comments['on_page']
            offset = (page - 1)*config.comments['on_page']
            params.extend([limit, offset])

        sql += where
        log.debug("SQL: {}".format(sql))

        self._result = await conn.execute(sql, params)
        return self

    @property
    async def rows(self):
        if self._rows:
            return self._rows

        async for row in self._result:
            self._rows.append(dict(row))
        return self._rows

    async def __aiter__(self):

        return self._result
