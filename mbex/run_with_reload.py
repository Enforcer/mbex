import uvicorn

from mbex.main import initialize

if __name__ == "__main__":
    app = initialize()
    uvicorn.run(app="mbex.main:initialize", host="127.0.0.1", port=8000, reload=True)
