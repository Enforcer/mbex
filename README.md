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

