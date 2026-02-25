import uuid

users_db = {}
sessions = {}

def register_user(username, password):
    if username in users_db:
        return {"status": "exists"}

    users_db[username] = password
    return {"status": "ok"}

def login_user(username, password):
    if users_db.get(username) != password:
        return {"status": "fail"}

    token = str(uuid.uuid4())
    sessions[token] = username

    return {"status": "ok", "token": token}

def get_user(token):
    return sessions.get(token)