"""Гененрация тестовых данных в базу"""

import random
import psycopg2

try:
    conn = psycopg2.connect(
        "dbname='comment_tree' user='comment_user' host='localhost' password='[etvjtcomm'")
except:
    print("I am unable to connect to the database")

MAX_NODES_CNT = 10**4
node_cnt = 1


def get_nextid():
    i = 0
    while True:
        i += 1
        yield i


id_seq = get_nextid()


def create_new_comment(parent_id='NULL', level=0):
    global node_cnt
    node_cnt += 1

    pk = next(id_seq)
    comment = "(%d, 'product', '1', %s, 1, md5(random()::text))" % (
        pk, str(parent_id))

    values = [comment]

    if level >= 100 or node_cnt >= 10**4:
        return values

    # добавляем ребенка или на том же уровне
    if random.random() > 0.3:
        new_parent_id = parent_id
    else:
        new_parent_id = pk
        level += 1

    # time.sleep(0.1)
    add = True
    # для большего ветвления пробуем добавить несколько
    while add and node_cnt <= MAX_NODES_CNT:
        values.extend(create_new_comment(new_parent_id, level))
        add = random.random() > 0.95

    return values


sql = """
    INSERT INTO comments_tbl
        (id, entity_type, entity_id, parent_id, user_id, text) VALUES
        %s;
"""
values = create_new_comment()
cur = conn.cursor()
sql = sql % ",\n".join(values)
sql += "ALTER SEQUENCE comments_tbl_id_seq RESTART 10001;"
cur.execute(sql)
conn.commit()
cur.close()
conn.close()
