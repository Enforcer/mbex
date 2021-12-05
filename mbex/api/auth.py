from fastapi import APIRouter, Header, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr

from mbex import auth

auth_router = APIRouter()


class CredsPayload(BaseModel):
    username: EmailStr
    password: str


@auth_router.post("/registration")
async def register(payload: CredsPayload) -> Response:
    try:
        await auth.register(payload.username, payload.password)
    except auth.UsernameTaken:
        return JSONResponse({"errors": ["Email already taken"]}, status_code=400)

    return Response(status_code=204)


@auth_router.post("/login")
async def login(payload: CredsPayload) -> Response:
    try:
        token = await auth.check_credentials(payload.username, payload.password)
    except auth.FailedAuthenticaiton:
        return JSONResponse({"errors": ["Credentials invalid"]}, status_code=400)

    return JSONResponse({"token": token}, status_code=200)


def current_user_id(authorization: str = Header(None)) -> auth.UserId:
    if not authorization:
        raise HTTPException(401)
    return auth.get_user_id_from_token(authorization)
