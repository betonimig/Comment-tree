
class DoesNotExists(Exception):
    """Requested record in database was not found"""
    pass


class CommentHasChild(Exception):
    """Deleted comment has children"""
    pass


class CommentDAO:
    """Class to handle data accessing of comment"""
    __table = 'comments_tbl'

    def __init__(self, user_id, entity_type, entity_id, text, pk=None,
                 created_dt=None, parent_id=None, path=None, level=None, 
                 username=None):
        self.pk = pk
        self.created_dt = created_dt
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.user_id = user_id
        self.username = username
        self.parent_id = parent_id
        self.path = path
        self.level = level
        self.text = text

    def __repr__(self):
        return str(self.__dict__)

    @staticmethod
    async def get_by_id(conn, id):
        """ Get comment from db by id"""

        sql = """
            SELECT
                comm.id as pk,
                to_json(created_dt) as created_dt,
                entity_type,
                entity_id,
                user_id,
                u.username,
                text,
                parent_id,
                ltree_path as path,
                nlevel(ltree_path) as level
            FROM {} comm, users_tbl u
            WHERE
                comm.user_id=u.id AND
                not is_removed AND comm.id=%s""".format(CommentDAO.__table)

        row = await (await conn.execute(sql, id)).fetchone()
        if not row:
            return None
        return CommentDAO(**row)

    async def save(self, conn):
        """INSERT or UPDATE comment"""

        if self.pk is None:
            await self._insert(conn)
        else:
            await self._update(conn)
        return self

    async def _insert(self, conn):
        """Insert comment to DB"""
        insert_sql = """
            INSERT INTO {} (
                parent_id,
                user_id,
                entity_type,
                entity_id,
                text
            ) VALUES (
                %s, %s, %s, %s, %s
            ) RETURNING
                id as pk,
                to_json(created_dt) as created_dt,
                ltree_path as path,
                nlevel(ltree_path) as level""".format(type(self).__table)

        select_parent_sql = """
            SELECT id
            FROM {}
            WHERE not is_removed AND id = %s
            FOR UPDATE""".format(type(self).__table)

        params = [self.parent_id, self.user_id, self.entity_type,
                  self.entity_id, self.text]

        # check user
        res = await conn.execute(
            "SELECT username FROM users_tbl WHERE id=%s",
            self.user_id)
        user = await res.fetchone()
        if user is None:
            raise DoesNotExists('User matching query does not exist.')

        async with conn.begin():
            # если есть родитель, то залочим его от удаления,
            # т.к. вставляем дочерний
            # в противном случае можем добавить дочерний удаленному родителю
            if self.parent_id is not None:
                res = await conn.execute(select_parent_sql, self.parent_id)
                if not res.rowcount:
                    raise DoesNotExists('Parent comment does not exists!')

            row = await (await conn.execute(insert_sql, *params)).fetchone()

        self.username = user.username
        self.__dict__.update(row)

    async def _update(self, conn):
        """Update comment"""
        sql = """
            UPDATE {} SET
                text=%s
            WHERE id=%s RETURNING id""".format(type(self).__table)

        params = [self.text, self.pk]
        res = await conn.execute(sql, params)
        if res.rowcount == 0:
            raise DoesNotExists('Comment does not exists!')

    async def delete(self, conn):
        """Delete comment from DB"""
        if self.pk is None:
            return None

        delete_sql = """
            UPDATE {}
            SET is_removed=true
            WHERE id=%s
        """.format(type(self).__table)

        async with conn.begin():
            # проверим нет ли дочерних
            res = await conn.execute(
                "SELECT id FROM comments_tbl WHERE parent_id=%s LIMIT 1",
                self.pk
            )
            if res.rowcount > 0:
                raise CommentHasChild("The comment has child comments!")

            res = await conn.execute(delete_sql, self.pk)

    def __iter__(self):
        return iter(self.__dict__.items())
