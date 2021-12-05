# Adding new dev package
```bash
poetry add --dev pytest-asyncio
```

# Adding new regular package
```bash
poetry add aioredis
```

# Exporting to requirements.txt
```bash
poetry export -f requirements.txt --without-hashes --dev --output requirements.txt
```

