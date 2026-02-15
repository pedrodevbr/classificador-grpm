"""
FastAPI backend for the Classificador de Materiais.
Replaces the Streamlit app with a REST API + SSE streaming.
"""
import os
import json
import base64
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from pydantic import BaseModel

from classificador import ClassificadorHierarquicoOpenRouter

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEFAULT_MODEL = "x-ai/grok-4.1-fast"
DATA_FILE = "data/grpms.xlsx"

AVAILABLE_MODELS = [
    "x-ai/grok-4.1-fast",
    "openai/gpt-4o-mini",
    "anthropic/claude-3-haiku",
    "google/gemini-3-flash-preview",
    "deepseek/deepseek-v3.2",
]

# ---------------------------------------------------------------------------
# Classifier cache (one instance per model)
# ---------------------------------------------------------------------------
_classifiers: dict[str, ClassificadorHierarquicoOpenRouter] = {}


def get_classifier(model: str) -> ClassificadorHierarquicoOpenRouter:
    """Return a cached classifier for the given model."""
    if model not in _classifiers:
        if not OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY não configurada no servidor.")
        clf = ClassificadorHierarquicoOpenRouter(api_key=OPENROUTER_API_KEY, model=model)
        if os.path.exists(DATA_FILE):
            clf.carregar_hierarquia(DATA_FILE)
        else:
            raise FileNotFoundError(f"Arquivo de dados '{DATA_FILE}' não encontrado.")
        _classifiers[model] = clf
    return _classifiers[model]


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load the default model on startup."""
    try:
        get_classifier(DEFAULT_MODEL)
        print(f"✅ Classificador carregado ({DEFAULT_MODEL})")
    except Exception as e:
        print(f"⚠️  Erro ao pré-carregar classificador: {e}")
    yield


app = FastAPI(title="Classificador de Materiais — ITAIPU", lifespan=lifespan)

# Serve static files (HTML/CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("static/index.html")


@app.get("/api/models")
async def list_models():
    return {"models": AVAILABLE_MODELS, "default": DEFAULT_MODEL}


class ClassifyRequest(BaseModel):
    descritivo: str
    model: str = DEFAULT_MODEL


@app.post("/api/classify")
async def classify(req: ClassifyRequest):
    """
    SSE endpoint that streams classification events.
    Each event is a JSON object with a `type` field.
    """
    if not req.descritivo.strip():
        raise HTTPException(status_code=400, detail="Descrição vazia.")

    try:
        clf = get_classifier(req.model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    def event_stream():
        for evento in clf.classificar_item(req.descritivo):
            # Serialize candidates (Pydantic objects → dicts)
            if evento["type"] == "candidates":
                opcoes = [
                    {"codigo": c.codigo, "descricao": c.descricao}
                    for c in evento["data"]["opcoes"]
                ]
                payload = {"type": "candidates", "data": {"opcoes": opcoes}}
            else:
                payload = evento

            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/describe-file")
async def describe_file(
    file: UploadFile = File(...),
    model: str = Form(DEFAULT_MODEL),
):
    """Process an uploaded PDF or image and return extracted/described text."""
    try:
        clf = get_classifier(model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    content = await file.read()

    if file.content_type == "application/pdf":
        import io
        text = clf.extrair_texto_pdf(io.BytesIO(content))
    elif file.content_type and file.content_type.startswith("image/"):
        text = clf.descrever_imagem(content, file.content_type)
    else:
        raise HTTPException(status_code=400, detail=f"Tipo de arquivo não suportado: {file.content_type}")

    return {"text": text}
