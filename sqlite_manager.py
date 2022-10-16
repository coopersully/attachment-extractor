import os
import sqlite3

conn: sqlite3.Connection
curr: sqlite3.Cursor


# Connects to the pre-existing database in the set directory.
# If the database does not exist in the set directory, one is
# created and then a connection is established.
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


# Creates the 'messages' table
def create_table():
    curr.execute("CREATE TABLE messages (uid integer, exported smallint, scanned smallint)")


# Accepts values for a complete entry in the 'messages' table.
# If an entry with the given UID already exists, it is updated to
# reflect the given values. If one does not exist, it is created.
def log(uid: int, exported_bool: bool, scanned_bool: bool):
    if exists(uid):
        log_update(uid, exported_bool, scanned_bool)
    else:
        log_new(uid, exported_bool, scanned_bool)


# Manually updates an entry in the 'messages' table.
def log_update(uid: int, exported_bool: bool, scanned_bool: bool):
    exported = bool_to_int(exported_bool)
    scanned = bool_to_int(scanned_bool)

    with conn:
        curr.execute(
            "UPDATE messages SET exported = :exported, scanned = :scanned WHERE uid = :uid",
            {'uid': uid, 'exported': exported, 'scanned': scanned}
        )


# Manually logs a new entry into the 'messages' table.
# WARNING! CAN CAUSE DUPLICATES. Use #log() instead!
def log_new(uid: int, exported_bool: bool, scanned_bool: bool):
    exported = bool_to_int(exported_bool)
    scanned = bool_to_int(scanned_bool)

    with conn:
        curr.execute(
            "INSERT INTO messages VALUES (:uid, :exported, :scanned)",
            {'uid': uid, 'exported': exported, 'scanned': scanned}
        )


# Queries if an entry with the given UID exists. Returns a boolean value.
def exists(uid: int):
    with conn:
        curr.execute("SELECT * FROM messages WHERE uid=:uid", {'uid': uid})
    return curr.fetchone() is not None


# Queries if an entry has been exported. Returns a boolean value.
def is_exported(uid: int):
    curr.execute("SELECT exported FROM messages WHERE uid=:uid", {'uid': uid})
    result = curr.fetchone()
    if result is None:
        return False
    return int_to_bool(result[0])


# Marks an entry as exported in the 'messages' table
def export(uid: int):
    if not exists(uid):
        log_new(uid, True, False)
    else:
        with conn:
            curr.execute("UPDATE messages SET exported = 1 WHERE uid = :uid", {'uid': uid})
        print(f'Logged export of {uid}')


# Queries if an entry has been scanned. Returns a boolean value.
def is_scanned(uid: int):
    curr.execute("SELECT scanned FROM messages WHERE uid=:uid", {'uid': uid})
    result = curr.fetchone()
    if result is None:
        return False
    return int_to_bool(result[0])


# Marks an entry as scanned in the 'messages' table
def scan(uid: int):
    if not exists(uid):
        log_new(uid, False, True)
    else:
        with conn:
            curr.execute("UPDATE messages SET scanned = 1 WHERE uid = :uid", {'uid': uid})
        print(f'Logged scanning of {uid}')


# Executes an SQL statement from the current Cursor
def execute_sql(command):
    with conn:
        curr.execute(command)
    return str(curr.fetchone())


# Converts an integer to a boolean value
def int_to_bool(value: int):
    return value > 0


# Converts a boolean value to an integer
def bool_to_int(value: bool):
    if value:
        return 1
    return 0


# Fetches the email in the database with the highest UID
# that has been exported and scanned; returns its uid (int).
def get_latest_email():
    with conn:
        curr.execute("SELECT max(uid) FROM messages WHERE exported = 1 AND scanned = 1")
    return curr.fetchone()


if __name__ == "__main__":
    create_or_connect()
    log(-1, True, False)

    print(f'Exported? {is_exported(-1)}, Scanned? {is_scanned(-1)}')
