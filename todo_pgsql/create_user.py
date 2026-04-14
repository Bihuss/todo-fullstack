from pwdlib import PasswordHash
import psycopg2

password_hash = PasswordHash.recommended()

conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="todo_db",
    user="postgres",
    password="kolega321"
)

cur = conn.cursor()

username = "michal2"
plain_password = "haslo123"
hashed_password = password_hash.hash(plain_password)

cur.execute(
    """
insert into users (username, hashed_password, disabled)
values (%s, %s, %s)
on conflict (username) do nothing
""",
(username, hashed_password, False)
)

conn.commit()
cur.close()
conn.close()

print("użytkownik dodany")