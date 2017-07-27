

class CommentHistoryDAO:
    """Class to handle data accessing of comment history"""

    def __init__(self, conn):
        self._conn = conn

    async def get_by_comment(self, comment_id):
        """Get history by comment"""
        sql = """
            SELECT
                id, comment_id, to_json(dt) as dtime, user_id, action, diff
            FROM comment_history_tbl
            WHERE comment_id=%s
            ORDER BY dt"""
        rows = []
        async for row in self._conn.execute(sql, comment_id):
            rows.append(dict(row))
        return rows

    async def insert(self, action, comment_id, user_id, diff):
        sql = """
            INSERT INTO comment_history_tbl
            (id, action, comment_id, user_id, diff)
            VALUES (DEFAULT, %s, %s, %s, %s)"""
        await self._conn.execute(sql, action, comment_id, user_id, str(diff))
