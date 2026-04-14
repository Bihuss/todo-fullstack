from db import get_connection
from psycopg2.extras import RealDictCursor

def get_tasks():
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT id, tekst, zrobione FROM tasks ORDER BY id;")
    tasks = cur.fetchall()

    cur.close()
    conn.close()
    return tasks


def add_task(tekst):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        INSERT INTO tasks (tekst, zrobione)
        VALUES (%s, %s)
        RETURNING id, tekst, zrobione;
        """,
        (tekst, False)
    )

    task = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()
    return task


def delete_task(task_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "DELETE FROM tasks WHERE id = %s RETURNING id;",
        (task_id,)
    )

    deleted = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return deleted


def mark_done(task_id):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        """
        UPDATE tasks
        SET zrobione = TRUE
        WHERE id = %s
        RETURNING id, tekst, zrobione;
        """,
        (task_id,)
    )

    updated = cur.fetchone()
    conn.commit()

    cur.close()
    conn.close()

    return updated