from fastapi import FastAPI

app = FastAPI(title="Mesa de Ayuda Inteligente")


@app.get("/health")
def health():
    return {"status": "ok"}
