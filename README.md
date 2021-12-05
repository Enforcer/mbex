# Install
```bash
python3.9 -m venv ve39
source ve39/bin/activate
pip install -r requirements.txt
```

# Run server
```bash
uvicorn mbex.main:initialize
```
Optionally, with reload like

```bash
uvicorn mbex.main:initialize --reload
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
