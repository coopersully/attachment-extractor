import os
import sqlite3

conn: sqlite3.Connection = None
curr: sqlite3.Cursor = None


def create_or_connect():
    global conn, curr
    did_exist = False
    if os.path.isfile("emails.db"):
        did_exist = True
    print('Connecting to database...')
    conn = sqlite3.connect("emails.db")
    curr = conn.cursor()
    if not did_exist:
        print('No database was found; creating a new database with \'messages\' table.')
        create_table()


def create_table():
    curr.execute("CREATE TABLE messages (uid integer, exported smallint, scanned smallint)")


def log(uid: int, exported_bool: bool, scanned_bool: bool):
    if exists(uid):
        log_update(uid, exported_bool, scanned_bool)
    else:
        log_new(uid, exported_bool, scanned_bool)


def log_update(uid: int, exported_bool: bool, scanned_bool: bool):

    exported = bool_to_int(exported_bool)
    scanned = bool_to_int(scanned_bool)

    with conn:
        curr.execute(
            "UPDATE messages SET exported = :exported, scanned = :scanned WHERE uid = :uid",
            {'uid': uid, 'exported': exported, 'scanned': scanned}
        )


def log_new(uid: int, exported_bool: bool, scanned_bool: bool):

    exported = bool_to_int(exported_bool)
    scanned = bool_to_int(scanned_bool)

    with conn:
        curr.execute(
            "INSERT INTO messages VALUES (:uid, :exported, :scanned)",
            {'uid': uid, 'exported': exported, 'scanned': scanned}
        )


def exists(uid: int):
    curr.execute("SELECT * FROM messages WHERE uid=:uid", {'uid': uid})
    return curr.fetchone() is not None


def is_exported(uid: int):
    curr.execute("SELECT exported FROM messages WHERE uid=:uid", {'uid': uid})
    result = curr.fetchone()
    if result is None:
        return False
    return int_to_bool(result[0])


def export(uid: int):
    if not exists(uid):
        log_new(uid, True, False)
    else:
        with conn:
            curr.execute("UPDATE messages SET exported = 1 WHERE uid = :uid", {'uid': uid})
        print(f'Logged export of {uid}')


def is_scanned(uid: int):
    curr.execute("SELECT scanned FROM messages WHERE uid=:uid", {'uid': uid})
    result = curr.fetchone()
    if result is None:
        return False
    return int_to_bool(result[0])


def scan(uid: int):
    if not exists(uid):
        log_new(uid, False, True)
    else:
        with conn:
            curr.execute("UPDATE messages SET scanned = 1 WHERE uid = :uid", {'uid': uid})
        print(f'Logged scanning of { uid }')


def execute_sql(command):
    with conn:
        curr.execute(command)
        return str(curr.fetchone())


def int_to_bool(value: int):
    return value == 1


def bool_to_int(value: bool):
    if value:
        return 1
    return 0


if __name__ == "__main__":
    create_or_connect()
    log(-1, True, False)

    print(f'Exported? { is_exported(-1) }, Scanned? { is_scanned(-1) }')