import oracledb
import tomllib

# Load secrets and config
with open("secrets.toml", "rb") as f:
    secret_data = tomllib.load(f)

with open("pyproject.toml", "rb") as f:
    config_data = tomllib.load(f)

database = secret_data["database"]["name"]
host = secret_data["database"]["host"]
service_name = secret_data["database"]["service_name"]
port = secret_data["database"]["port"]
db_user = secret_data["database"]["user"]
db_password = secret_data["database"]["password"]

# First connection: create and populate the table
with oracledb.connect(
    user=db_user,
    password=db_password,
    dsn=f"{host}:{port}/{service_name}",
    ssl_server_dn_match=True,
    protocol="tcps"
) as conn:
    print("Connected:", conn.version)

    with conn.cursor() as cur:
        try:
            cur.execute("DROP TABLE users PURGE")
        except oracledb.DatabaseError:
            pass

        cur.execute("""
            CREATE TABLE users (
                username VARCHAR2(50) PRIMARY KEY,
                role VARCHAR2(20),
                email VARCHAR2(50)
            )
        """)

        cur.execute("INSERT INTO users VALUES ('alice', 'admin', 'alice@example.com')")
        cur.execute("INSERT INTO users VALUES ('bob', 'dev', 'bob@example.com')")
        cur.execute("INSERT INTO users VALUES ('carol', 'analyst', 'carol@example.com')")

    conn.commit()

# Second connection: query the table
with oracledb.connect(
    user=secret_data["database"]["user"],
    password=secret_data["database"]["password"],
    dsn=f"{host}:{port}/{service_name}",
    ssl_server_dn_match=True,
    protocol="tcps"
) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT username, role, email FROM users")
        for row in cur:
            print(row)

