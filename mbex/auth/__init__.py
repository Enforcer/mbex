import bcrypt
import jwt

from mbex import redis

USERS = {}
JWT_TOKEN_SECRET = "TestSecretYo"
REDIS_KEY = "users"

JwtToken = str
UserId = str


async def clear():
    async with redis.conn() as c:
        await c.delete(REDIS_KEY)


class UsernameTaken(Exception):
    pass


class FailedAuthenticaiton(Exception):
    pass


class NoSuchUser(FailedAuthenticaiton):
    pass


class PasswordInvalid(FailedAuthenticaiton):
    pass


async def register(username: str, password: str) -> None:
    async with redis.conn() as c:
        stored_pw = await c.hget(REDIS_KEY, username)

        if stored_pw is not None:
            raise UsernameTaken
        else:
            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=13))
            await c.hset(REDIS_KEY, username, hashed_pw)


async def check_credentials(username: str, password: str) -> JwtToken:
    async with redis.conn() as c:
        stored_pw = await c.hget(REDIS_KEY, username)

    if stored_pw is None:
        raise NoSuchUser
    else:
        password_ok = bcrypt.checkpw(password.encode(), stored_pw)
        if password_ok:
            return jwt.encode(
                {"user_id": username}, JWT_TOKEN_SECRET, algorithm="HS256"
            )
        else:
            raise PasswordInvalid


def get_user_id_from_token(token: JwtToken) -> UserId:
    decoded = jwt.decode(token, JWT_TOKEN_SECRET, algorithms=["HS256"])
    return decoded["user_id"]
