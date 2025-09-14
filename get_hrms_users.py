import json
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

# Select users and save as json
with oracledb.connect(
    user=db_user,
    password=db_password,
    dsn=f"{host}:{port}/{service_name}",
    ssl_server_dn_match=True,
    protocol="tcps"
) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT username, role FROM users")
        user_list = []
        for row in cur:
            user_list.append({"username": row[0], "role": row[1]})
        with open("users.json", "w") as f:
            json.dump(user_list, f, indent=2)

