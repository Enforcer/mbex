# Prerequisites
## Install
```bash
python3.9 -m venv ve39
source ve39/bin/activate
pip install -r requirements.txt
pip install poetry
poetry install
```

## Running redis
Application requires a running redis instance. You can use docker:
```bash
docker run --rm --name redis -p 6379:6379 redis:latest
```


# Run server
```bash
python mbex/run_without_reload.py
```
Optionally, with hot-code reload like

```bash
python mbex/run_with_reload.py
```

# Checking out API docs
Go to `http://localhost:8000/docs` with server running

# Running tests
WARNING: start redis first
```bash
pytest
```


# Tips
If you want to line-profile view functions, apply `@profile` decorator first, like:
```
@auth_router.post("/registration")
@profile  # <--- here!
async def register(payload: CredsPayload) -> Response:
    try:
        await auth.register(payload.username, payload.password)
    except auth.UsernameTaken:
        return JSONResponse({"errors": ["Email already taken"]}, status_code=400)

    return Response(status_code=204)
```
