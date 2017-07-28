"""Гененрация тестовых данных в базу"""

import random
import psycopg2


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

    if level >= 100 or node_cnt >= 10**4:
        return []

    pk = next(id_seq)
    comment = "(%d, 'product', '1', %s, 1, md5(random()::text))" % (
        pk, str(parent_id))

    values = [comment]

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


def main():
    try:
        conn = psycopg2.connect(
            "dbname='comment_tree' user='comment_user' host='localhost' password='[etvjtcomm'")
    except:
        print("I am unable to connect to the database")

    cur = conn.cursor()
    cur.execute("""
        DELETE FROM comment_history_tbl;
        DELETE FROM comments_tbl;
        DELETE FROM users_tbl;
        ALTER SEQUENCE comments_tbl_id_seq RESTART 1;""")
    conn.commit()
    sql = """
        INSERT INTO "users_tbl" VALUES (1, 'test1'), (2, 'test2'), (3, 'test3');
        INSERT INTO comments_tbl
            (id, entity_type, entity_id, parent_id, user_id, text) VALUES
            %s;
    """
    values = create_new_comment()
    values.append("(10002, 'product', 1, NULL, 1, 'Test comment')")
    sql = sql % ",".join(values)
    sql += "ALTER SEQUENCE comments_tbl_id_seq RESTART 10003;"

    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()


if __name__ == '__main__':
    main()
